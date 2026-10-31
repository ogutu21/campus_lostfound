from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from .forms import SettingsForm, VerifyForm

MAX_ATTEMPTS = 5


def login_page(request):
    """Just a page with the Google button. Google does the real work."""
    if request.user.is_authenticated:
        return redirect("items:list")
    return render(request, "accounts/login.html", {"next": request.GET.get("next", "")})


@login_required
def verify(request):
    user = request.user
    if user.id_number:
        return redirect("items:list")

    form = VerifyForm()
    if user.verify_attempts < MAX_ATTEMPTS and request.method == "POST":
        form = VerifyForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user.id_number = form.cleaned_data["registration_number"]
                    user.save()
                    form.entry.used_by = user
                    form.entry.save()
            except IntegrityError:
                user.id_number = None
                form.add_error(None, "That number was just taken by someone else.")
            else:
                messages.success(request, f"Welcome, {user.first_name}! You're verified.")
                return redirect("items:list")
        # A wrong guess counts against the user.
        user.verify_attempts += 1
        user.save(update_fields=["verify_attempts"])

    return render(request, "accounts/verify.html", {
        "form": form,
        "locked": user.verify_attempts >= MAX_ATTEMPTS,
        "left": max(MAX_ATTEMPTS - user.verify_attempts, 0),
    })


@login_required
def account_settings(request):
    if request.method == "POST":
        form = SettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved.")
            return redirect("accounts:settings")
    else:
        form = SettingsForm(instance=request.user)
    return render(request, "accounts/settings.html", {"form": form})