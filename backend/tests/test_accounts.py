"""Tests for the account and verification flow.

Run with:  python manage.py test tests
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Profile, VerificationCode

User = get_user_model()

STRONG_PASSWORD = "Sunflower-Ritual-2026"


@override_settings(DEBUG=True)
class RegistrationTests(TestCase):
    """Sign-up issues a code and never returns it outside development."""

    def setUp(self):
        self.client = APIClient()

    def register(self, **overrides):
        payload = {
            "email": "ada@example.com",
            "password": STRONG_PASSWORD,
            "full_name": "Ada Obi",
            **overrides,
        }
        return self.client.post("/api/auth/register/", payload, format="json")

    def test_register_creates_unverified_user_and_emails_a_code(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email="ada@example.com")
        self.assertFalse(user.profile.email_verified)
        self.assertTrue(VerificationCode.objects.filter(user=user).exists())

        # No Resend key locally, so the code comes back for testing (DEBUG only).
        self.assertRegex(response.data["debug_code"], r"^\d{6}$")
        self.assertFalse(response.data["email_sent"])

    def test_code_is_never_returned_in_production(self):
        with override_settings(DEBUG=False):
            response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("debug_code", response.data)

    def test_duplicate_email_is_rejected(self):
        self.register()
        response = self.register()
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_weak_password_is_rejected(self):
        response = self.register(password="123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)

    def test_code_is_stored_hashed_not_plain(self):
        self.register()
        code = VerificationCode.objects.get().code_hash
        self.assertNotIn(code, {"123456", "000000"})
        self.assertNotEqual(len(code), 6)


@override_settings(DEBUG=True)
class VerifyEmailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.post(
            "/api/auth/register/",
            {"email": "ada@example.com", "password": STRONG_PASSWORD},
            format="json",
        )
        self.user = User.objects.get(email="ada@example.com")

    def test_correct_code_verifies_and_signs_in(self):
        _, code = VerificationCode.issue(self.user, VerificationCode.SIGNUP)
        response = self.client.post(
            "/api/auth/verify-email/", {"email": self.user.email, "code": code}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_verified)

    def test_wrong_code_is_rejected_and_counted(self):
        VerificationCode.issue(self.user, VerificationCode.SIGNUP)
        response = self.client.post(
            "/api/auth/verify-email/", {"email": self.user.email, "code": "000000"}, format="json"
        )

        self.assertEqual(response.status_code, 400)

        # Only the active code counts; issuing a new one burns the previous row.
        active = VerificationCode.objects.filter(consumed_at__isnull=True).latest("created_at")
        self.assertEqual(active.attempts, 1)


    def test_code_is_burned_after_max_attempts(self):
        VerificationCode.issue(self.user, VerificationCode.SIGNUP)
        for _ in range(5):
            self.client.post(
                "/api/auth/verify-email/",
                {"email": self.user.email, "code": "000000"},
                format="json",
            )

        burned = VerificationCode.objects.filter(consumed_at__isnull=False).exists()
        self.assertTrue(burned, "the code should be burned once the attempt budget runs out")

        # A freshly issued code still works, proving the burned row cannot be reused.
        _, code = VerificationCode.issue(self.user, VerificationCode.SIGNUP)
        response = self.client.post(
            "/api/auth/verify-email/", {"email": self.user.email, "code": code}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_unknown_email_gives_the_same_answer_as_a_wrong_code(self):
        response = self.client.post(
            "/api/auth/verify-email/", {"email": "nobody@example.com", "code": "123456"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("debug_code", response.data)

    def test_expired_code_is_rejected(self):
        code_obj, code = VerificationCode.issue(self.user, VerificationCode.SIGNUP)
        code_obj.expires_at = timezone.now() - timedelta(minutes=1)
        code_obj.save(update_fields=["expires_at"])

        response = self.client.post(
            "/api/auth/verify-email/", {"email": self.user.email, "code": code}, format="json"
        )
        self.assertEqual(response.status_code, 400)


class SignInTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="ada", email="ada@example.com", password=STRONG_PASSWORD
        )
        Profile.objects.get_or_create(user=self.user)

    def test_sign_in_with_email(self):
        response = self.client.post(
            "/api/auth/login/",
            {"identifier": "ada@example.com", "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertIn("email_verified", response.data["user"])

    def test_sign_in_with_username_and_mixed_case_email(self):
        for identifier in ("ada", "ADA@EXAMPLE.COM"):
            response = self.client.post(
                "/api/auth/login/",
                {"identifier": identifier, "password": STRONG_PASSWORD},
                format="json",
            )
            self.assertEqual(response.status_code, 200, identifier)

    def test_wrong_password_and_unknown_user_give_the_same_error(self):
        wrong = self.client.post(
            "/api/auth/login/", {"identifier": "ada@example.com", "password": "nope"}, format="json"
        )
        missing = self.client.post(
            "/api/auth/login/", {"identifier": "ghost@example.com", "password": "nope"}, format="json"
        )

        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.data, missing.data, "sign-in must not reveal which accounts exist")

    def test_inactive_user_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            "/api/auth/login/", {"identifier": "ada", "password": STRONG_PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_me_requires_a_token(self):
        """403 rather than 401: SessionAuthentication is listed first and offers
        no ``WWW-Authenticate`` challenge, which is DRF's documented behaviour."""
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)


    def test_me_returns_the_signed_in_user(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "ada@example.com")

    def test_email_cannot_be_changed_through_the_profile(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.patch(
            "/api/auth/me/", {"email": "attacker@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "ada@example.com", "email must be read-only")

    def test_logout_deletes_the_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 200)
        self.assertFalse(Token.objects.filter(key=token.key).exists())


class TokenExpiryTests(TestCase):
    """Tokens used to live forever; a stolen one must stop working."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="ada", email="ada@example.com", password=STRONG_PASSWORD
        )
        self.token = Token.objects.create(user=self.user)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    @override_settings(AUTH_TOKEN_TTL=60)
    def test_expired_token_is_rejected_and_deleted(self):
        self.token.created = timezone.now() - timedelta(seconds=120)
        self.token.save(update_fields=["created"])
        self.authenticate()

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())


    @override_settings(AUTH_TOKEN_TTL=3600)
    def test_fresh_token_is_accepted(self):
        self.authenticate()
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)


class PasswordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="ada", email="ada@example.com", password=STRONG_PASSWORD
        )
        Profile.objects.get_or_create(user=self.user)

    def test_reset_request_does_not_reveal_whether_the_address_exists(self):
        known = self.client.post(
            "/api/auth/password/reset/", {"email": "ada@example.com"}, format="json"
        )
        unknown = self.client.post(
            "/api/auth/password/reset/", {"email": "ghost@example.com"}, format="json"
        )

        self.assertEqual(known.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(known.data["detail"], unknown.data["detail"])

    def test_reset_confirm_changes_the_password_and_rotates_tokens(self):
        old_token = Token.objects.create(user=self.user)
        _, code = VerificationCode.issue(self.user, VerificationCode.RESET)
        new_password = "Harvest-Moon-2026"

        response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {"email": "ada@example.com", "code": code, "new_password": new_password},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(Token.objects.filter(key=old_token.key).exists())
        self.assertNotEqual(response.data["token"], old_token.key)

    def test_change_password_requires_the_current_one(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        wrong = self.client.post(
            "/api/auth/password/change/",
            {"current_password": "nope", "new_password": "Harvest-Moon-2026"},
            format="json",
        )
        self.assertEqual(wrong.status_code, 400)

        right = self.client.post(
            "/api/auth/password/change/",
            {"current_password": STRONG_PASSWORD, "new_password": "Harvest-Moon-2026"},
            format="json",
        )
        self.assertEqual(right.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Harvest-Moon-2026"))


