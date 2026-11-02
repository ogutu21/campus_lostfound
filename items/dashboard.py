from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import RosterEntry
from accounts.views import MAX_ATTEMPTS

from .models import Claim, Item, Report

User = get_user_model()


def staff_only(view):
    """Signed-in staff only. Everyone else gets 'forbidden'."""
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("Staff only.")
        return view(request, *args, **kwargs)
    return wrapper


@staff_only
def dashboard(request):
    week_ago = timezone.now() - timedelta(days=7)
    open_reports = Report.objects.filter(handled=False)

    stats = {
        "members": User.objects.count(),
        "verified": User.objects.filter(id_number__isnull=False).count(),
        "lost": Item.objects.filter(kind=Item.Kind.LOST, status=Item.Status.ACTIVE,
                                    is_hidden=False).count(),
        "found": Item.objects.filter(kind=Item.Kind.FOUND, status=Item.Status.ACTIVE,
                                     is_hidden=False).count(),
        "resolved": Item.objects.filter(status=Item.Status.RESOLVED).count(),
        "hidden": Item.objects.filter(is_hidden=True).count(),
        "new_week": Item.objects.filter(created_at__gte=week_ago).count(),
        "claims_waiting": Claim.objects.filter(status=Claim.Status.PENDING).count(),
        "roster_total": RosterEntry.objects.count(),
        "roster_used": RosterEntry.objects.filter(used_by__isnull=False).count(),
        "reports_open": open_reports.count(),
    }

    return render(request, "items/dashboard.html", {
        "stats": stats,
        "reports": open_reports.select_related("item", "item__poster", "reporter")[:20],
        "locked": User.objects.filter(verify_attempts__gte=MAX_ATTEMPTS),
    })


@staff_only
@require_POST
def report_resolve(request, pk):
    report = get_object_or_404(Report.objects.select_related("item"), pk=pk)
    action = request.POST.get("action")

    if action == "hide":
        report.item.is_hidden = True
        report.item.save(update_fields=["is_hidden"])
        # Every open report about that post is dealt with by hiding it.
        Report.objects.filter(item=report.item, handled=False).update(handled=True)
        messages.success(request, "Post hidden. Its reports are marked handled.")
    elif action == "dismiss":
        report.handled = True
        report.save(update_fields=["handled"])
        messages.success(request, "Report dismissed.")
    else:
        messages.error(request, "Unknown action.")
    return redirect("items:dashboard")


@staff_only
@require_POST
def unlock_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.verify_attempts = 0
    user.save(update_fields=["verify_attempts"])
    messages.success(request, f"{user.get_full_name()} can try verifying again.")
    return redirect("items:dashboard")