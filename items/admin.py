from django.contrib import admin

from .models import Comment, Item, Message, Thread


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "category", "location", "poster", "status", "created_at")
    list_filter = ("kind", "category", "status")
    search_fields = ("title", "description", "location")


admin.site.register(Comment)
admin.site.register(Thread)
admin.site.register(Message)