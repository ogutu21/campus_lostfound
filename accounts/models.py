from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Knows how to create users when the login field is id_number."""
    use_in_migrations = True

    def get_by_natural_key(self, id_number):
        # Used by the admin login. iexact = case-insensitive exact match.
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
    # Empty until the person proves their registration number after
    # their first Google sign-in. NULL (not "") so many users can be
    # unverified at once without breaking the unique rule.
    id_number = models.CharField(
        "Registration number", max_length=30, unique=True,
        null=True, blank=True,
        help_text="Student registration or staff ID number",
    )
    email_notifications = models.BooleanField(
        "Email me about replies, messages and claims", default=True,
    )
    verify_attempts = models.PositiveSmallIntegerField(
        "Wrong registration numbers entered", default=0,
        help_text="Locked out at 5. Set back to 0 to unlock.",
    )

    USERNAME_FIELD = "id_number"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        # Store the number uppercase; store "no number" as NULL.
        if self.id_number:
            self.id_number = self.id_number.strip().upper()
        else:
            self.id_number = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.id_number or self.email})"


class RosterEntry(models.Model):
    """One valid registration number. Anyone not on the roster cannot join."""
    number = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120, blank=True)
    used_by = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="roster_entry",
    )

    class Meta:
        ordering = ["number"]
        verbose_name_plural = "roster entries"

    def save(self, *args, **kwargs):
        self.number = self.number.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number