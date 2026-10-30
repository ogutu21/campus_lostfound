from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms

from .models import User


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("id_number", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

    def clean_id_number(self):
        # Runs automatically for the id_number field.
        return self.cleaned_data["id_number"].strip().upper()


class LoginForm(AuthenticationForm):
    def clean_username(self):
        # The login field is always called "username" inside this form,
        # even though it holds the ID number.
        return self.cleaned_data["username"].strip().upper()


class SettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "email_notifications")
        labels = {"email": "Email address"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True