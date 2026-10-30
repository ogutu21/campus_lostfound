from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Knows how to create users when the login field is id_number."""
    use_in_migrations = True

    def get_by_natural_key(self, id_number):
        # Django's login calls this to find the user.
        # iexact = case-insensitive exact match.
        return self.get(id_number__iexact=id_number.strip())

    def _create_user(self, id_number, password, **extra_fields):
        if not id_number:
            raise ValueError("An ID number is required")
        user = self.model(id_number=id_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, id_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(id_number, password, **extra_fields)

    def create_superuser(self, id_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(id_number, password, **extra_fields)


class User(AbstractUser):
    username = None
    id_number = models.CharField(
        "ID number", max_length=30, unique=True,
        help_text="Student or staff ID number",
    )
    email_notifications = models.BooleanField(
        "Email me about replies, messages and claims", default=True,
    )

    USERNAME_FIELD = "id_number"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        # Whatever path created this user (form, admin, shell), store it uppercase.
        self.id_number = self.id_number.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.id_number})"