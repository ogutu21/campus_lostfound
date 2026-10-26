from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, ItemForm, MessageForm
from .models import Comment, Item, Thread


def item_list(request):
    items = Item.objects.filter(status=Item.Status.ACTIVE).select_related("poster")

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
            return redirect("items:detail", pk=item.pk)
    else:
        form = CommentForm()

    return render(request, "items/item_detail.html", {
        "item": item, "comments": comments, "form": form,
    })


@login_required
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.poster = request.user
            item.save()
            messages.success(request, "Your post has been published.")
            return redirect("items:detail", pk=item.pk)
    else:
        form = ItemForm()
    return render(request, "items/item_form.html", {"form": form, "heading": "Post an item"})


@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.poster != request.user:
        return HttpResponseForbidden("You can only edit your own posts.")
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated.")
            return redirect("items:detail", pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, "items/item_form.html", {"form": form, "heading": "Edit post"})


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


# ---------- Private messaging ----------

@login_required
@require_POST
def thread_start(request, pk):
    """Open (or reuse) a private conversation with the poster of item `pk`."""
    item = get_object_or_404(Item, pk=pk)
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
        # The "other person" in this conversation, for display.
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

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.thread = thread
            msg.sender = request.user
            msg.save()
            thread.save(update_fields=["updated_at"])   # bumps it to the top of the inbox
            return redirect("items:thread", pk=thread.pk)
    else:
        form = MessageForm()

    # Opening the conversation marks the other person's messages as read.
    thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    other = thread.item.poster if request.user.pk == thread.starter_id else thread.starter
    return render(request, "items/thread_detail.html", {
        "thread": thread,
        "chat": thread.messages.select_related("sender"),
        "form": form,
        "other": other,
    })