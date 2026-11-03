from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render

from .models import Claim, Item


@login_required
def my_posts(request):
    """Everything the signed-in user has posted, in one place."""
    show = "resolved" if request.GET.get("show") == "resolved" else "active"
    status = Item.Status.RESOLVED if show == "resolved" else Item.Status.ACTIVE

    mine = Item.objects.filter(poster=request.user)
    items = (
        mine.filter(status=status)
        .annotate(
            comment_count=Count("comments", distinct=True),
            pending_claims=Count(
                "claims", filter=Q(claims__status=Claim.Status.PENDING), distinct=True
            ),
        )
    )

    page_obj = Paginator(items, 20).get_page(request.GET.get("page"))

    return render(request, "items/my_posts.html", {
        "page_obj": page_obj,
        "show": show,
        "active_total": mine.filter(status=Item.Status.ACTIVE).count(),
        "resolved_total": mine.filter(status=Item.Status.RESOLVED).count(),
    })