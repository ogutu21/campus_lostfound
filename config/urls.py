from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),

    # allauth brings its own password pages. Google is the only way in,
    # so send those to our login page BEFORE allauth's URLs are included.
    path("auth/login/", RedirectView.as_view(pattern_name="accounts:login")),
    path("auth/signup/", RedirectView.as_view(pattern_name="accounts:login")),
    path("auth/password/reset/", RedirectView.as_view(pattern_name="accounts:login")),
    path("auth/", include("allauth.urls")),

    path("", include("items.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)