"""Django-admin registration for the account models."""

from django.contrib import admin

from .models import Address, Profile, VerificationCode


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Read-only view of customer delivery addresses.

    A saved address is a convenience for the customer, not a system of record -
    each order keeps its own copy - so staff can inspect them but not create or
    edit them here.
    """

    list_display = ("full_name", "phone", "city", "state", "label", "is_default", "user")
    list_filter = ("label", "is_default")
    search_fields = ("user__email", "full_name", "phone", "line1", "city", "state")
    list_select_related = ("user",)
    readonly_fields = tuple(f.name for f in Address._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email_verified", "marketing_opt_in", "created_at")
    list_filter = ("email_verified", "marketing_opt_in")
    search_fields = ("user__username", "user__email", "phone")
    list_select_related = ("user",)


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    """Read-only view of codes.

    The stored value is a password hash, so it is intentionally not shown or
    editable - this page is only useful for auditing that codes are issued and
    then burned.
    """

    list_display = ("user", "purpose", "created_at", "expires_at", "attempts", "consumed_at")
    list_filter = ("purpose",)
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "user",
        "purpose",
        "code_hash",
        "expires_at",
        "attempts",
        "consumed_at",
        "created_at",
    )
    list_select_related = ("user",)

    def has_add_permission(self, request):
        return False

