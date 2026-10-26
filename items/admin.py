from django.contrib import admin

from .models import Comment, Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "category", "location", "poster", "status", "created_at")
    list_filter = ("kind", "category", "status")
    search_fields = ("title", "description", "location")


admin.site.register(Comment)