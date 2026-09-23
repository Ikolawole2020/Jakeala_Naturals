"""Serializers for registration, sign-in, verification and profile edits."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Profile

User = get_user_model()


def username_from_email(email):
    """Derive a unique username from an email address.

    Accounts are identified by email, but ``auth.User`` still requires a unique
    username, so one is generated and de-duplicated (``ada@x.com`` -> ``ada``,
    ``ada2``, ``ada3``...). Users never have to think about it: sign-in accepts
    either the email or this handle.
    """
    base = (email or "").split("@")[0].strip().lower() or "customer"
    base = "".join(ch for ch in base if ch.isalnum() or ch in "._-")[:30] or "customer"

    candidate = base
    suffix = 1
    while User.objects.filter(username__iexact=candidate).exists():
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("phone", "marketing_opt_in", "email_verified")
        read_only_fields = ("email_verified",)


class UserSerializer(serializers.ModelSerializer):
    """The shape of the signed-in user returned to the front end."""

    phone = serializers.CharField(source="profile.phone", required=False, allow_blank=True)
    marketing_opt_in = serializers.BooleanField(
        source="profile.marketing_opt_in", required=False
    )
    email_verified = serializers.BooleanField(source="profile.email_verified", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "marketing_opt_in",
            "email_verified",
            "date_joined",
        )
        read_only_fields = ("id", "username", "email", "date_joined")

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if profile_data:
            profile, _ = Profile.objects.get_or_create(user=instance)
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()
        return instance


class RegisterSerializer(serializers.Serializer):
    """Sign-up input. Password strength is enforced by Django's validators."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=140)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    marketing_opt_in = serializers.BooleanField(required=False, default=False)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with that email already exists. Try signing in instead."
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]
        full_name = (validated_data.get("full_name") or "").strip()
        first, _, last = full_name.partition(" ")

        user = User.objects.create_user(
            username=username_from_email(email),
            email=email,
            password=validated_data["password"],
            first_name=first[:150],
            last_name=last[:150],
        )

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone = validated_data.get("phone", "") or ""
        profile.marketing_opt_in = validated_data.get("marketing_opt_in", False)
        profile.email_verified = False
        profile.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Sign-in input. ``identifier`` accepts an email address or a username."""

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class EmailCodeSerializer(serializers.Serializer):
    """A code sent by email, plus the address it belongs to."""

    email = serializers.EmailField()
    code = serializers.CharField(min_length=4, max_length=12, trim_whitespace=True)


class PasswordResetConfirmSerializer(EmailCodeSerializer):
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Change the password of the signed-in user."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is not correct.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Ask for a password-reset code. Only the address is needed."""

    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class ResendCodeSerializer(serializers.Serializer):
    """Ask for a fresh sign-up or reset code."""

    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=("signup", "reset"), default="signup")

    def validate_email(self, value):
        return value.strip().lower()

