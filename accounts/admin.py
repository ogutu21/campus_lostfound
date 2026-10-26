from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id_number", "first_name", "last_name", "email", "is_staff")
    search_fields = ("id_number", "first_name", "last_name", "email")
    ordering = ("id_number",)

    fieldsets = (
        (None, {"fields": ("id_number", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("id_number", "first_name", "last_name", "email",
                       "password1", "password2"),
        }),
    )