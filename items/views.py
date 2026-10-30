from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ClaimForm, CommentForm, ItemForm, MessageForm, ReportForm
from .models import Claim, Comment, Item, Message, Report, Thread
from .notifications import notify


def _place_suggestions():
    """The ten most-used locations, offered as suggestions in the post form."""
    rows = (
        Item.objects.values("location")
        .annotate(n=Count("id"))
        .order_by("-n", "location")[:10]
    )
    return [r["location"] for r in rows]


def item_list(request):
    items = (
        Item.objects.filter(status=Item.Status.ACTIVE, is_hidden=False)
        .select_related("poster")
    )

    kind = request.GET.get("kind", "")
    category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()

    if kind in (Item.Kind.LOST, Item.Kind.FOUND):
        items = items.filter(kind=kind)

    if category in Item.Category.values:
        items = items.filter(category=category)

    if query:
        items = items.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
        )

    paginator = Paginator(items, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "items/item_list.html", {
        "page_obj": page_obj,
        "kind": kind,
        "category": category,
        "query": query,
        "categories": Item.Category.choices,
        "filter_qs": params.urlencode(),
    })


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)

    # Hidden posts are visible only to their poster and to staff.
    if item.is_hidden and request.user != item.poster and not request.user.is_staff:
        raise Http404

    comments = item.comments.select_related("author")

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.item = item
            comment.author = request.user
            comment.save()
            if item.poster_id != request.user.pk:
                notify(
                    item.poster,
                    f'New comment on "{item.title}"',
                    f"{request.user.get_full_name()} commented on your post:\n\n{comment.body}",
                    reverse("items:detail", args=[item.pk]),
                )
            return redirect("items:detail", pk=item.pk)
    else:
        form = CommentForm()

    user_claim = None
    if request.user.is_authenticated:
        user_claim = Claim.objects.filter(item=item, claimant=request.user).first()

    return render(request, "items/item_detail.html", {
        "item": item, "comments": comments, "form": form, "user_claim": user_claim,
    })


@login_required
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.poster = request.user
            item.save()
            if item.kind == Item.Kind.FOUND:
                messages.success(
                    request,
                    f"Posted as No. {item.pk}. When someone claims it, you'll see it under Claims.",
                )
            else:
                messages.success(
                    request,
                    f"Posted as No. {item.pk}. If someone finds it, they'll message you.",
                )
            return redirect("items:detail", pk=item.pk)
    else:
        # The home page buttons send ?kind=LOST or ?kind=FOUND.
        kind = request.GET.get("kind", "")
        initial = {"kind": kind} if kind in Item.Kind.values else None
        form = ItemForm(initial=initial)

    return render(request, "items/item_form.html", {
        "form": form,
        "heading": "Post an item",
        "submit_label": "Publish post",
        "place_suggestions": _place_suggestions(),
    })


@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.poster != request.user:
        return HttpResponseForbidden("You can only edit your own posts.")
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Changes saved.")
            return redirect("items:detail", pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, "items/item_form.html", {
        "form": form,
        "heading": "Edit post",
        "submit_label": "Save changes",
        "place_suggestions": _place_suggestions(),
    })


@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.poster != request.user:
        return HttpResponseForbidden("You can only delete your own posts.")
    if request.method == "POST":
        item.delete()
        messages.success(request, "Post deleted.")
        return redirect("items:list")
    return render(request, "items/item_confirm_delete.html", {"item": item})


@login_required
@require_POST
def item_resolve(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.poster != request.user:
        return HttpResponseForbidden("You can only resolve your own posts.")
    item.status = Item.Status.RESOLVED
    item.save()
    messages.success(request, "Marked as resolved.")
    return redirect("items:detail", pk=item.pk)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author != request.user and comment.item.poster != request.user:
        return HttpResponseForbidden("You can't delete this comment.")
    item_pk = comment.item.pk
    comment.delete()
    return redirect("items:detail", pk=item_pk)


# ---------- Reporting ----------

@login_required
def report_create(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if item.poster == request.user:
        messages.info(request, "You can't report your own post.")
        return redirect("items:detail", pk=item.pk)

    if Report.objects.filter(item=item, reporter=request.user).exists():
        messages.info(request, "You have already reported this post. Thank you.")
        return redirect("items:list")

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.item = item
            report.reporter = request.user
            report.save()
            messages.success(request, "Thank you. A moderator will review your report.")
            return redirect("items:list")
    else:
        form = ReportForm()

    return render(request, "items/report_form.html", {"form": form, "item": item})


# ---------- Claims ----------

@login_required
def claim_create(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.is_hidden:
        raise Http404

    if item.poster == request.user:
        messages.info(request, "This is your own post.")
        return redirect("items:detail", pk=item.pk)
    if item.kind != Item.Kind.FOUND:
        messages.info(request, "Only found items can be claimed.")
        return redirect("items:detail", pk=item.pk)
    if Claim.objects.filter(item=item, claimant=request.user).exists():
        messages.info(request, "You have already claimed this item.")
        return redirect("items:detail", pk=item.pk)
    if item.status != Item.Status.ACTIVE:
        messages.info(request, "This item has already been resolved.")
        return redirect("items:detail", pk=item.pk)

    if request.method == "POST":
        form = ClaimForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.claimant = request.user
            claim.save()
            notify(
                item.poster,
                f'Someone wants to claim "{item.title}"',
                "A student says this item is theirs. Review their answer, "
                "then approve or reject the claim.",
                reverse("items:claims"),
            )
            messages.success(request, "Your claim was sent. The finder will review your answer.")
            return redirect("items:detail", pk=item.pk)
    else:
        form = ClaimForm()

    question = item.verification_question or (
        "Describe the item in detail so the finder can confirm it is yours."
    )
    return render(request, "items/claim_form.html", {
        "form": form, "item": item, "question": question,
    })


@login_required
def claims_received(request):
    claims = list(
        Claim.objects.filter(item__poster=request.user)
        .select_related("item", "claimant")
    )
    pending = [c for c in claims if c.status == Claim.Status.PENDING]
    decided = [c for c in claims if c.status != Claim.Status.PENDING]
    return render(request, "items/claims_received.html", {
        "pending": pending, "decided": decided,
    })


@login_required
@require_POST
def claim_decide(request, pk):
    claim = get_object_or_404(
        Claim.objects.select_related("item", "claimant"), pk=pk
    )
    if claim.item.poster != request.user:
        return HttpResponseForbidden("Only the finder can decide on this claim.")
    if claim.status != Claim.Status.PENDING:
        messages.info(request, "This claim has already been decided.")
        return redirect("items:claims")

    action = request.POST.get("action")

    if action == "approve":
        claim.status = Claim.Status.APPROVED
        claim.save()
        thread, _created = Thread.objects.get_or_create(
            item=claim.item, starter=claim.claimant
        )
        Message.objects.create(
            thread=thread,
            sender=request.user,
            body=(
                f'Your claim on "{claim.item.title}" was approved. '
                "Let's arrange how and where to hand it over."
            ),
        )
        thread.save(update_fields=["updated_at"])
        notify(
            claim.claimant,
            f'Your claim on "{claim.item.title}" was approved',
            "The finder accepted your answer. Message them to arrange the handover.",
            reverse("items:thread", args=[thread.pk]),
        )
        messages.success(request, "Claim approved. You can now arrange the handover here.")
        return redirect("items:thread", pk=thread.pk)

    if action == "reject":
        claim.status = Claim.Status.REJECTED
        claim.save()
        notify(
            claim.claimant,
            f'Your claim on "{claim.item.title}" was not approved',
            "The finder couldn't confirm this item is yours from your answer.",
            reverse("items:detail", args=[claim.item.pk]),
        )
        messages.success(request, "Claim rejected.")
        return redirect("items:claims")

    messages.error(request, "Unknown action.")
    return redirect("items:claims")


# ---------- Private messaging ----------

@login_required
@require_POST
def thread_start(request, pk):
    """Open (or reuse) a private conversation with the poster of item `pk`."""
    item = get_object_or_404(Item, pk=pk)
    if item.is_hidden:
        raise Http404
    if item.poster == request.user:
        messages.info(request, "This is your own post, so there is nobody to message.")
        return redirect("items:detail", pk=item.pk)
    thread, _created = Thread.objects.get_or_create(item=item, starter=request.user)
    return redirect("items:thread", pk=thread.pk)


@login_required
def inbox(request):
    user = request.user
    threads = list(
        Thread.objects.filter(Q(starter=user) | Q(item__poster=user))
        .select_related("item", "item__poster", "starter")
        .annotate(unread=Count(
            "messages",
            filter=Q(messages__is_read=False) & ~Q(messages__sender=user),
        ))
    )
    for t in threads:
        t.other = t.item.poster if user.pk == t.starter_id else t.starter
    return render(request, "items/inbox.html", {"threads": threads})


@login_required
def thread_detail(request, pk):
    thread = get_object_or_404(
        Thread.objects.select_related("item", "item__poster", "starter"), pk=pk
    )
    # Authorization: only the two people in the conversation may open it.
    if request.user.pk not in (thread.starter_id, thread.item.poster_id):
        return HttpResponseForbidden("This conversation is private.")

    other = thread.item.poster if request.user.pk == thread.starter_id else thread.starter

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            # If my earlier messages are still unread, the other person has
            # already been emailed, so don't send another email.
            already_notified = thread.messages.filter(
                sender=request.user, is_read=False
            ).exists()

            msg = form.save(commit=False)
            msg.thread = thread
            msg.sender = request.user
            msg.save()
            thread.save(update_fields=["updated_at"])

            if not already_notified:
                notify(
                    other,
                    f'New message about "{thread.item.title}"',
                    f"{request.user.get_full_name()} sent you a private message.",
                    reverse("items:thread", args=[thread.pk]),
                )
            return redirect("items:thread", pk=thread.pk)
    else:
        form = MessageForm()

    thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    return render(request, "items/thread_detail.html", {
        "thread": thread,
        "chat": thread.messages.select_related("sender"),
        "form": form,
        "other": other,
    })