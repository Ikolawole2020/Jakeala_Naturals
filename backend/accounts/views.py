"""Account endpoints: registration, email verification, sign-in, password reset.

Three rules hold throughout this module:

* **Codes are generated here, never in the browser.** A code minted client-side
  could be forged with DevTools, which would make verification worthless.
* **Who may call what is explicit.** The credential endpoints are ``AllowAny``
  (they are the only way to obtain a token); everything else requires a token.
* **Every endpoint is rate limited** with a named scope from
  ``config/throttles.py``. Codes are stored hashed, single-use and expiring.

The generated code is echoed back in the response **only** in DEBUG and only when
EmailJS is unconfigured, so sign-up can be tested locally before the mail service
is wired up. Production never returns it.
"""

import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from config.throttles import AuthThrottle, EmailIPThrottle, EmailThrottle

from .models import Profile, VerificationCode
from .serializers import (
    ChangePasswordSerializer,
    EmailCodeSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendCodeSerializer,
    UserSerializer,
)
from .services import send_password_reset_code, send_verification_code

User = get_user_model()
logger = logging.getLogger(__name__)

# Returned by password-reset endpoints whether or not the address exists, so the
# API cannot be used to discover who has an account.
GENERIC_RESET_SENT = (
    "If that email address has an account, we've sent a 6-digit code to it."
)
GENERIC_CODE_FAILED = "That code is not correct or has expired. Please request a new one."


def profile_for(user):
    """Return the user's profile, creating it if an older row predates the signal."""
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def issue_token(user):
    """Return this user's API token, restarting its expiry clock.

    DRF keeps one token per user. Re-using it (rather than minting a new one on
    every sign-in) keeps a session on another device alive, while refreshing
    ``created`` means the TTL is measured from the most recent sign-in.
    """
    token, created = Token.objects.get_or_create(user=user)
    if not created:
        token.created = timezone.now()
        token.save(update_fields=["created"])
    return token


def rotate_token(user):
    """Invalidate every existing token and issue a fresh one.

    Used after a password change or reset: changing a password must also evict
    anyone holding a stolen token.
    """
    Token.objects.filter(user=user).delete()
    return Token.objects.create(user=user)


def code_payload(user, code, sent, purpose):
    """Shared "we sent you a code" response body."""
    payload = {
        "email": user.email,
        "purpose": purpose,
        "email_sent": sent,
        "ttl_minutes": settings.VERIFICATION_CODE_TTL_MINUTES,
    }
    if not sent and settings.DEBUG:
        payload["debug_code"] = code
    return payload


def auth_response(user, token=None):
    """The body returned after a successful sign-in or verification."""
    token = token or issue_token(user)
    return {"token": token.key, "user": UserSerializer(user).data}


# --------------------------------------------------------------------------- #
#  Registration + email verification                                          #
# --------------------------------------------------------------------------- #
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle, EmailThrottle, EmailIPThrottle])
def register(request):
    """Create an unverified account and email a 6-digit code."""
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()

    _, code = VerificationCode.issue(user, VerificationCode.SIGNUP)
    sent = send_verification_code(user, code)

    return Response(
        {
            "detail": (
                "We've sent a 6-digit code to your email. "
                "Enter it below to activate your account."
            ),
            **code_payload(user, code, sent, VerificationCode.SIGNUP),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def verify_email(request):
    """Check the sign-up code and hand back a token, signing the user in."""
    ser = EmailCodeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    email = ser.validated_data["email"].strip().lower()

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        # Same message and status as a wrong code: no account enumeration.
        return Response({"detail": GENERIC_CODE_FAILED}, status=status.HTTP_400_BAD_REQUEST)

    ok, message = VerificationCode.consume(
        user, VerificationCode.SIGNUP, ser.validated_data["code"]
    )
    if not ok:
        if profile_for(user).email_verified:
            # Already verified on an earlier attempt; treat as success.
            return Response(auth_response(user))
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    profile = profile_for(user)
    profile.email_verified = True
    profile.save(update_fields=["email_verified"])

    return Response(
        {"detail": "Your email is verified. Welcome to Jakeala Naturals.", **auth_response(user)}
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([EmailThrottle, EmailIPThrottle])
def resend_code(request):
    """Issue a fresh sign-up or password-reset code, invalidating the old one."""
    ser = ResendCodeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    email = ser.validated_data["email"]
    purpose = ser.validated_data["purpose"]

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return Response({"detail": GENERIC_RESET_SENT})

    if purpose == VerificationCode.SIGNUP and profile_for(user).email_verified:
        return Response({"detail": "That email is already verified. You can sign in."})

    _, code = VerificationCode.issue(user, purpose)
    if purpose == VerificationCode.SIGNUP:
        sent = send_verification_code(user, code)
    else:
        sent = send_password_reset_code(user, code)

    return Response(
        {"detail": "We've sent you a new code.", **code_payload(user, code, sent, purpose)}
    )


# --------------------------------------------------------------------------- #
#  Sign in / out                                                              #
# --------------------------------------------------------------------------- #
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login(request):
    """Sign in with an email address or username.

    Unverified accounts may sign in (so a lost code never locks anyone out of
    their own order history); the response carries ``email_verified`` so the
    front end can prompt them to finish verification.
    """
    ser = LoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    identifier = ser.validated_data["identifier"].strip()
    password = ser.validated_data["password"]

    user = authenticate(request, username=identifier, password=password)
    if user is None:
        # The backend already matches email or username; retry through the exact
        # stored username in case the address differs only by letter case.
        candidate = User.objects.filter(email__iexact=identifier).first()
        if candidate is not None:
            user = authenticate(request, username=candidate.username, password=password)

    if user is None or not user.is_active:
        # One message for both failures: never reveal which accounts exist.
        return Response(
            {"detail": "That email/username and password combination is not correct."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    logger.info("Sign-in succeeded for user id=%s", user.pk)
    return Response(auth_response(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Delete the caller's tokens, ending every session for that account."""
    Token.objects.filter(user=request.user).delete()
    return Response({"detail": "You've been signed out."})


# --------------------------------------------------------------------------- #
#  Signed-in profile                                                          #
# --------------------------------------------------------------------------- #
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """Read or update the signed-in user's profile.

    Only ``first_name``, ``last_name``, ``phone`` and ``marketing_opt_in`` are
    writable - ``UserSerializer`` marks email, username and ``email_verified``
    read-only, so nobody can re-point an account at another address.
    """
    if request.method == "PATCH":
        ser = UserSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()

    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the signed-in user's password and evict all other sessions."""
    ser = ChangePasswordSerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)

    user = request.user
    user.set_password(ser.validated_data["new_password"])
    user.save(update_fields=["password"])

    token = rotate_token(user)
    return Response(
        {"detail": "Your password has been updated.", "token": token.key},
    )


# --------------------------------------------------------------------------- #
#  Password reset                                                             #
# --------------------------------------------------------------------------- #
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([EmailThrottle, EmailIPThrottle])
def password_reset_request(request):
    """Email a reset code. Always reports success, whether or not the address exists."""
    ser = PasswordResetRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    email = ser.validated_data["email"]

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    payload = {"detail": GENERIC_RESET_SENT}

    if user is not None:
        _, code = VerificationCode.issue(user, VerificationCode.RESET)
        sent = send_password_reset_code(user, code)
        payload.update(code_payload(user, code, sent, VerificationCode.RESET))

    return Response(payload)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def password_reset_confirm(request):
    """Consume the reset code, set the new password and sign the user in."""
    ser = PasswordResetConfirmSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    email = ser.validated_data["email"].strip().lower()

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return Response({"detail": GENERIC_CODE_FAILED}, status=status.HTTP_400_BAD_REQUEST)

    ok, message = VerificationCode.consume(
        user, VerificationCode.RESET, ser.validated_data["code"]
    )
    if not ok:
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(ser.validated_data["new_password"])
    user.save(update_fields=["password"])

    # A reset proves control of the inbox, so treat the address as verified.
    profile = profile_for(user)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])

    token = rotate_token(user)
    logger.info("Password reset completed for user id=%s", user.pk)
    return Response(
        {
            "detail": "Your password has been reset. You're signed in.",
            **auth_response(user, token),
        }
    )



