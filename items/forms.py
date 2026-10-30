from django import forms
from django.utils import timezone

from .models import Claim, Comment, Item, Message, Report

MAX_IMAGE_MB = 5


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["kind", "title", "description", "category",
                  "location", "date_occurred", "image", "verification_question"]
        widgets = {
            "kind": forms.RadioSelect,
            "title": forms.TextInput(attrs={"placeholder": "e.g. Black phone with a cracked case"}),
            "date_occurred": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "location": forms.TextInput(attrs={"list": "places", "autocomplete": "off"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        # The date picker won't let people choose a day in the future.
        self.fields["date_occurred"].widget.attrs["max"] = today.isoformat()
        # New posts start with today's date filled in.
        if not self.instance.pk:
            self.fields["date_occurred"].initial = today

    def clean_date_occurred(self):
        date = self.cleaned_data["date_occurred"]
        if date > timezone.localdate():
            raise forms.ValidationError("The date can't be in the future.")
        return date

    def clean_image(self):
        image = self.cleaned_data.get("image")
        # A freshly uploaded file has content_type; an unchanged existing
        # image (when editing) does not, so we skip it.
        if image and hasattr(image, "content_type"):
            if image.size > MAX_IMAGE_MB * 1024 * 1024:
                raise forms.ValidationError(f"Photo must be smaller than {MAX_IMAGE_MB} MB.")
            if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise forms.ValidationError("Please upload a JPG, PNG or WebP image.")
        return image

    def clean(self):
        cleaned = super().clean()
        question = (cleaned.get("verification_question") or "").strip()
        if cleaned.get("kind") == Item.Kind.FOUND and not question:
            self.add_error(
                "verification_question",
                "Found items need a verification question, so only the real owner can claim it.",
            )
        return cleaned


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a comment..."})}
        labels = {"body": ""}


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a private message..."})}
        labels = {"body": ""}


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "details"]
        widgets = {"details": forms.Textarea(attrs={"rows": 3})}
        labels = {"details": "Anything else a moderator should know? (optional)"}


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ["answer"]
        widgets = {"answer": forms.Textarea(attrs={"rows": 4})}
        labels = {"answer": "Your answer"}