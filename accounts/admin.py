from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AdminUserCreationForm
from .models import RosterEntry, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    ordering = ("id_number",)
    list_display = ("id_number", "first_name", "last_name", "email", "verify_attempts", "is_staff")
    search_fields = ("id_number", "first_name", "last_name", "email")

    fieldsets = (
        (None, {"fields": ("id_number", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email",
                                      "email_notifications", "verify_attempts")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("id_number", "first_name", "last_name", "email",
                           "password1", "password2")}),
    )


@admin.register(RosterEntry)
class RosterEntryAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "used_by")
    search_fields = ("number", "name")