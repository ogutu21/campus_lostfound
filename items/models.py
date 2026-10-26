from django.conf import settings
from django.db import models


class Item(models.Model):
    class Kind(models.TextChoices):
        LOST = "LOST", "Lost"
        FOUND = "FOUND", "Found"

    class Category(models.TextChoices):
        ELECTRONICS = "ELECTRONICS", "Electronics"
        DOCUMENTS = "DOCUMENTS", "ID cards & documents"
        BOOKS = "BOOKS", "Books & stationery"
        CLOTHING = "CLOTHING", "Clothing & bags"
        KEYS = "KEYS", "Keys"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Still looking"
        RESOLVED = "RESOLVED", "Resolved"

    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    kind = models.CharField(max_length=5, choices=Kind.choices)
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices,
                                default=Category.OTHER)
    location = models.CharField(max_length=150,
                                help_text="Where it was lost or found, e.g. Library 2nd floor")
    date_occurred = models.DateField(help_text="Date it was lost or found")
    image = models.ImageField(upload_to="items/%Y/%m/", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_kind_display()}] {self.title}"


class Comment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="comments")
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.id_number} on {self.item.title}"


class Thread(models.Model):
    """A private conversation about one item, between its poster and one other user."""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="threads")
    starter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="started_threads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]   # most recently active first
        constraints = [
            models.UniqueConstraint(fields=["item", "starter"],
                                    name="one_thread_per_item_per_starter"),
        ]

    def __str__(self):
        return f"{self.starter.id_number} about {self.item.title}"


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="sent_messages")
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.id_number}: {self.body[:30]}"