from django import forms

from .models import Comment, Item

MAX_IMAGE_MB = 5


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["kind", "title", "description", "category",
                  "location", "date_occurred", "image"]
        widgets = {
            "date_occurred": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a comment..."})}
        labels = {"body": ""}