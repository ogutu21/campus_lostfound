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
    verification_question = models.CharField(
        "Verification question",
        max_length=200,
        blank=True,
        help_text=(
            "Required for found items. Ask something only the real owner would know "
            "(e.g. 'What is on the lock screen?'). Do NOT put the answer in the description."
        ),
    )
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.ACTIVE)
    is_hidden = models.BooleanField(
        default=False,
        help_text="Hidden by a moderator. Only the poster and staff can see it.",
    )
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
        ordering = ["-updated_at"]
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


class Report(models.Model):
    """One person flagging one post for a moderator to review."""

    class Reason(models.TextChoices):
        FAKE = "FAKE", "Fake or misleading post"
        INAPPROPRIATE = "INAPPROPRIATE", "Inappropriate content"
        SPAM = "SPAM", "Spam"
        PERSONAL = "PERSONAL", "Shows someone's private information"
        OTHER = "OTHER", "Other"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="reports_made")
    reason = models.CharField(max_length=15, choices=Reason.choices)
    details = models.TextField(max_length=500, blank=True)
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["handled", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["item", "reporter"],
                                    name="one_report_per_item_per_reporter"),
        ]

    def __str__(self):
        return f"{self.get_reason_display()} - {self.item.title}"


class Claim(models.Model):
    """Someone saying 'this found item is mine', with an answer to the verification question."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Waiting for the finder"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="claims")
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="claims_made")
    answer = models.TextField(max_length=1000)
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["item", "claimant"],
                                    name="one_claim_per_item_per_claimant"),
        ]

    def __str__(self):
        return f"{self.claimant.id_number} claims {self.item.title}"