from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, ItemForm
from .models import Comment, Item


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

    paginator = Paginator(items, 10)                       # 10 posts per page
    page_obj = paginator.get_page(request.GET.get("page"))  # safe for bad page numbers

    # Rebuild the filters as a query string, minus "page", for the Next/Previous links.
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