"""
ClaimForm (Class Diagram 3).

FR-17: an ownership explanation is required.
UI-01: validation errors are shown for invalid / incomplete claim data.
"""
from django import forms

from .models import ClaimRequest

MIN_MESSAGE_LENGTH = 20
MAX_MESSAGE_LENGTH = 1000


class ClaimForm(forms.ModelForm):
    class Meta:
        model = ClaimRequest
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "maxlength": MAX_MESSAGE_LENGTH,
                    "minlength": MIN_MESSAGE_LENGTH,
                    "data-counter": "true",
                    "placeholder": "Describe identifying details only the owner would know "
                    "(stickers, scratches, contents, lock-screen, when/where you lost it)...",
                }
            )
        }

    def clean_message(self):
        message = (self.cleaned_data.get("message") or "").strip()
        if not message:
            raise forms.ValidationError("An ownership explanation is required.")
        if len(message) < MIN_MESSAGE_LENGTH:
            raise forms.ValidationError(
                f"Please give a more detailed explanation (at least {MIN_MESSAGE_LENGTH} characters)."
            )
        if len(message) > MAX_MESSAGE_LENGTH:
            raise forms.ValidationError(f"Please keep the explanation under {MAX_MESSAGE_LENGTH} characters.")
        return message

    def save(self, item=None, claimant=None, commit=True):
        """+save(item, claimant) : ClaimRequest"""
        claim = super().save(commit=False)
        if item is not None:
            claim.item = item
        if claimant is not None:
            claim.claimant = claimant
        if commit:
            claim.save()
        return claim
