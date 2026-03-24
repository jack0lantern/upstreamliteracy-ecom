from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Address, AuditLog, EmailVerificationToken, Institution, PasswordResetToken, User, UserProfile


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    fields = ["phone", "preferences"]


class InstitutionInline(admin.StackedInline):
    model = Institution
    can_delete = False
    verbose_name_plural = "Institution"
    fk_name = "user"
    fields = ["school_name", "district_name", "tax_exempt", "exemption_cert", "exemption_verified"]


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, InstitutionInline]

    list_display = ["email", "first_name", "last_name", "role", "is_verified", "is_active", "is_staff", "date_joined"]
    list_filter = ["role", "is_verified", "is_active", "is_staff", "is_guest"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    readonly_fields = ["date_joined", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "role")},
        ),
        (
            _("Status"),
            {"fields": ("is_active", "is_staff", "is_superuser", "is_verified", "is_guest")},
        ),
        (
            _("Permissions"),
            {"fields": ("groups", "user_permissions")},
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )

    # BaseUserAdmin uses 'username' by default; override for email-based model
    USERNAME_FIELD = "email"


# ---------------------------------------------------------------------------
# Address Admin
# ---------------------------------------------------------------------------


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "label", "recipient_name", "city", "state", "country", "is_default"]
    list_filter = ["state", "country", "is_default"]
    search_fields = ["user__email", "recipient_name", "city", "zip"]
    raw_id_fields = ["user"]


# ---------------------------------------------------------------------------
# AuditLog Admin (read-only)
# ---------------------------------------------------------------------------


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor_email", "action", "target_type", "target_id", "ip_address"]
    list_filter = ["action", "target_type"]
    search_fields = ["actor_email", "action", "target_type", "target_id", "ip_address"]
    readonly_fields = [
        "actor",
        "actor_email",
        "action",
        "target_type",
        "target_id",
        "ip_address",
        "metadata",
        "created_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Token Admins (lightweight)
# ---------------------------------------------------------------------------


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at"]
    raw_id_fields = ["user"]
    readonly_fields = ["created_at"]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at", "used"]
    list_filter = ["used"]
    raw_id_fields = ["user"]
    readonly_fields = ["token_hash", "created_at"]

    def has_change_permission(self, request, obj=None):
        return False
