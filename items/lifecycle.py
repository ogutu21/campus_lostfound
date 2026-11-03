import hmac
import os
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import GRACE_DAYS, REMIND_AFTER_DAYS, Item
from .notifications import notify


def run_lifecycle(remind_after=REMIND_AFTER_DAYS, grace=GRACE_DAYS, dry_run=False):
    """Take down posts whose reminder went unanswered, then remind the next batch.

    With dry_run=True nothing is changed and no email is sent: it only counts.
    """
    now = timezone.now()
    remind_cutoff = now - timedelta(days=remind_after)
    grace_cutoff = now - timedelta(days=grace)
    result = {"expired": 0, "reminded": 0, "failed": 0}

    # 1. Reminded long enough ago and never renewed: take it down.
    #    (Renewing clears reminded_at, so renewed posts never match here.)
    to_expire = Item.objects.filter(
        status=Item.Status.ACTIVE, reminded_at__lte=grace_cutoff
    ).select_related("poster")
    for item in to_expire:
        result["expired"] += 1
        if dry_run:
            continue
        Item.objects.filter(pk=item.pk).update(status=Item.Status.EXPIRED)
        notify(
            item.poster,
            f'Your post "{item.title}" was taken down',
            "We didn't hear back after our reminder, so we removed it from the "
            "public list. Nothing is lost. If you still need it, open My posts, "
            "go to the Expired tab, and tap Renew to put it back.",
            reverse("items:mine") + "?show=expired",
            always=True,
        )

    # 2. Old posts nobody has confirmed lately: send a reminder.
    due = (
        Item.objects.filter(
            status=Item.Status.ACTIVE, is_hidden=False, reminded_at__isnull=True
        )
        .filter(
            Q(last_confirmed_at__lte=remind_cutoff)
            | Q(last_confirmed_at__isnull=True, created_at__lte=remind_cutoff)
        )
        .select_related("poster")
    )
    for item in due:
        if dry_run:
            result["reminded"] += 1
            continue
        sent = notify(
            item.poster,
            f'Is "{item.title}" still unresolved?',
            f'Your {item.get_kind_display().lower()} post "{item.title}" has been up '
            f"for over {remind_after} days.\n\n"
            "Still looking? Tap Renew so people keep seeing it.\n"
            "Got it back, or don't need it any more? Mark it resolved.\n\n"
            f"If we don't hear from you in {grace} days, it comes down from the "
            "public list. You can always put it back.",
            reverse("items:mine"),
            always=True,
        )
        if sent:
            # Only mark it reminded if the email really went out, so a mail
            # problem never makes a post disappear unannounced.
            Item.objects.filter(pk=item.pk).update(reminded_at=now)
            result["reminded"] += 1
        else:
            result["failed"] += 1

    return result


@login_required
@require_POST
def renew(request, pk):
    """The poster says 'yes, I'm still looking': restart the clock."""
    item = get_object_or_404(Item, pk=pk)
    if item.poster != request.user:
        return HttpResponseForbidden("You can only renew your own posts.")
    if item.status == Item.Status.RESOLVED:
        messages.info(request, "That post is resolved. Post again if you need to.")
        return redirect("items:mine")

    item.status = Item.Status.ACTIVE
    item.last_confirmed_at = timezone.now()
    item.reminded_at = None
    item.save(update_fields=["status", "last_confirmed_at", "reminded_at", "updated_at"])
    messages.success(request, f"Renewed. It stays up for another {REMIND_AFTER_DAYS} days.")
    return redirect("items:mine")


@login_required
@require_POST
def run_now(request):
    """Staff button on the dashboard: preview or run the housekeeping."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Staff only.")
    dry = request.POST.get("dry_run") == "1"
    r = run_lifecycle(dry_run=dry)
    prefix = "Preview only, nothing changed. Would send" if dry else "Done. Sent"
    messages.success(
        request,
        f"{prefix} {r['reminded']} reminder(s) and take down {r['expired']} post(s)."
        + (f" {r['failed']} email(s) failed and will be retried." if r["failed"] else ""),
    )
    return redirect("items:dashboard")


@csrf_exempt
@require_POST
def cron_run(request, token):
    """Called once a day by an outside timer. The secret token is the password."""
    expected = os.environ.get("CRON_TOKEN", "")
    if not expected or not hmac.compare_digest(token.encode(), expected.encode()):
        raise Http404
    return JsonResponse(run_lifecycle())