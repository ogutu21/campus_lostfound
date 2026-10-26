from django.db.models import Q

from .models import Message


def unread_messages(request):
    """Makes `unread_count` available in every template (for the nav badge)."""
    if request.user.is_authenticated:
        count = (
            Message.objects.filter(is_read=False)
            .filter(Q(thread__starter=request.user) | Q(thread__item__poster=request.user))
            .exclude(sender=request.user)
            .count()
        )
        return {"unread_count": count}
    return {"unread_count": 0}