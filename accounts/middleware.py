from django.shortcuts import redirect
from django.urls import reverse


class RequireRegistrationNumberMiddleware:
    """Signed in with Google but no registration number yet? Send them to
    the verification page. Nothing else on the site opens until they pass."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.id_number:
            path = request.path
            allowed = {reverse("accounts:verify"), reverse("accounts:logout")}
            if path not in allowed and not path.startswith(("/admin/", "/static/", "/media/")):
                return redirect("accounts:verify")
        return self.get_response(request)