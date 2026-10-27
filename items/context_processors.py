from django.db.models import Q

from .models import Claim, Message


def unread_messages(request):
    """Adds `unread_count` and `pending_claims` to every template (for the nav badges)."""
    if request.user.is_authenticated:
        unread = (
            Message.objects.filter(is_read=False)
            .filter(Q(thread__starter=request.user) | Q(thread__item__poster=request.user))
            .exclude(sender=request.user)
            .count()
        )
        pending = Claim.objects.filter(
            item__poster=request.user, status=Claim.Status.PENDING
        ).count()
        return {"unread_count": unread, "pending_claims": pending}
    return {"unread_count": 0, "pending_claims": 0}