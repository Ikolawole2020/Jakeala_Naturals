"""Account models: profiles and single-use verification codes.

This project keeps Django's stock ``auth.User`` rather than swapping in a custom
user model. A `AUTH_USER_MODEL` change cannot be done safely on a database that
is already live and seeded, and everything we need hangs off a ``Profile``
(OneToOne) plus short-lived ``VerificationCode`` rows instead.

Verification codes are **never stored in plain text**: only a password-hash of
the 6 digits is persisted, so a database leak does not hand an attacker working
codes. Complexity is low (10^6) which is exactly why the row also carries a
short TTL, an attempt counter, and a single-use marker.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def generate_code():
    """Return a cryptographically random 6-digit string ('100000'-'999999')."""
    return str(secrets.randbelow(900000) + 100000)


class Profile(models.Model):
    """Extra account fields that do not belong on ``auth.User``."""

    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=40, blank=True)
    marketing_opt_in = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "customer profile"

    def __str__(self):
        return f"Profile for {self.user.username}"


class VerificationCode(models.Model):
    """A one-time code sent by email for sign-up or password reset."""

    SIGNUP = "signup"
    RESET = "reset"
    PURPOSE_CHOICES = [
        (SIGNUP, "Sign-up email verification"),
        (RESET, "Password reset"),
    ]

    user = models.ForeignKey(User, related_name="verification_codes", on_delete=models.CASCADE)
    purpose = models.CharField(max_length=16, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "purpose", "consumed_at"])]

    def __str__(self):
        return f"{self.get_purpose_display()} for {self.user.email or self.user.username}"

    # ------------------------------------------------------------------ issue
    @classmethod
    def issue(cls, user, purpose):
        """Create a fresh code and invalidate any earlier unused one.

        Returns ``(instance, plain_code)``. The plain code is returned exactly
        once so it can be emailed; it is never persisted or re-readable.
        """
        cls.objects.filter(
            user=user, purpose=purpose, consumed_at__isnull=True
        ).update(consumed_at=timezone.now())

        code = generate_code()
        instance = cls.objects.create(
            user=user,
            purpose=purpose,
            code_hash=make_password(code),
            expires_at=timezone.now()
            + timedelta(minutes=settings.VERIFICATION_CODE_TTL_MINUTES),
        )
        return instance, code

    # ----------------------------------------------------------------- verify
    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def _burn(self, *, save=True):
        self.consumed_at = timezone.now()
        if save:
            self.save(update_fields=["consumed_at"])

    @classmethod
    def consume(cls, user, purpose, code):
        """Validate ``code`` and burn it. Returns ``(ok, message)``.

        Every failure path counts against the attempt budget so a wrong guess is
        never free, and the code is destroyed once the budget runs out.
        """
        code = (code or "").strip()
        instance = (
            cls.objects.filter(user=user, purpose=purpose, consumed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if instance is None:
            return False, "That code is no longer valid. Please request a new one."

        if instance.is_expired:
            instance._burn()
            return False, "That code has expired. Please request a new one."

        if instance.attempts >= settings.VERIFICATION_MAX_ATTEMPTS:
            instance._burn()
            return False, "Too many incorrect attempts. Please request a new code."

        if not check_password(code, instance.code_hash):
            instance.attempts += 1
            fields = ["attempts"]
            if instance.attempts >= settings.VERIFICATION_MAX_ATTEMPTS:
                instance.consumed_at = timezone.now()
                fields.append("consumed_at")
            instance.save(update_fields=fields)
            left = max(0, settings.VERIFICATION_MAX_ATTEMPTS - instance.attempts)
            if not left:
                return False, "Too many incorrect attempts. Please request a new code."
            return False, f"That code is not correct. {left} attempt(s) remaining."

        instance._burn()
        return True, ""


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """Every user gets a profile, including the superuser made by ``seed``."""
    if created:
        Profile.objects.get_or_create(user=instance)
