from django.contrib import admin

from .models import Comment, Item, Message, Report, Thread


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "category", "location", "poster",
                    "status", "is_hidden", "created_at")
    list_filter = ("kind", "category", "status", "is_hidden")
    search_fields = ("title", "description", "location")
    actions = ["hide_posts", "unhide_posts"]

    @admin.action(description="Hide selected posts from the public")
    def hide_posts(self, request, queryset):
        queryset.update(is_hidden=True)

    @admin.action(description="Unhide selected posts")
    def unhide_posts(self, request, queryset):
        queryset.update(is_hidden=False)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("item", "reason", "reporter", "handled", "created_at")
    list_filter = ("handled", "reason")
    search_fields = ("item__title", "details")
    actions = ["mark_handled", "hide_reported_posts"]

    @admin.action(description="Mark selected reports as handled")
    def mark_handled(self, request, queryset):
        queryset.update(handled=True)

    @admin.action(description="Hide the posts named in the selected reports")
    def hide_reported_posts(self, request, queryset):
        Item.objects.filter(reports__in=queryset).update(is_hidden=True)


admin.site.register(Comment)
admin.site.register(Thread)
admin.site.register(Message)