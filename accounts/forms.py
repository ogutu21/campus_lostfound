from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import RosterEntry, User


class VerifyForm(forms.Form):
    registration_number = forms.CharField(
        label="Student registration number", max_length=30,
        widget=forms.TextInput(attrs={"autocomplete": "off", "autofocus": True}),
    )

    def clean_registration_number(self):
        number = self.cleaned_data["registration_number"].strip().upper()

        entry = RosterEntry.objects.filter(number=number).first()
        if entry is None:
            raise forms.ValidationError(
                "We couldn't find that number. Check it and try again."
            )
        if entry.used_by_id or User.objects.filter(id_number__iexact=number).exists():
            raise forms.ValidationError(
                "That number is already linked to an account. If it's yours, "
                "ask the site admin for help."
            )
        self.entry = entry   # the view uses this
        return number


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email_notifications",)


class AdminUserCreationForm(UserCreationForm):
    """Only used by the admin's 'add user' page."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("id_number", "first_name", "last_name", "email")