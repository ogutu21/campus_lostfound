from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_page, name="login"),
    # Registration is now Google sign-in. Old links just go to the login page.
    path("register/", RedirectView.as_view(pattern_name="accounts:login"), name="register"),
    path("verify/", views.verify, name="verify"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("settings/", views.account_settings, name="settings"),
]