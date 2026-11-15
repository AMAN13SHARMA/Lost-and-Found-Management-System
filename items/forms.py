"""
ItemForm (Class Diagram 2) and the search / filter form.

FR-07: collect title, report type, category, description, location,
       date lost/found and contact method (all required).
FR-08: optional collection point and photograph.
FR-09 / NFR-03 / NFR-11: reject photos > 5 MB or with a content type other
       than JPEG, PNG or WebP.
UI-01: validation errors are displayed for invalid / incomplete reports.
"""
from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils import timezone

from .models import CAMPUS_LOCATIONS, CATEGORY_CHOICES, Item, ReportType


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "report_type",
            "title",
            "category",
            "description",
            "location",
            "date_lost_found",
            "contact_method",
            "collection_point",
            "photo",
        ]
        widgets = {
            "report_type": forms.RadioSelect,
            "title": forms.TextInput(attrs={"placeholder": "e.g. Black HP laptop charger"}),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Colour, brand, distinguishing marks, contents..."}
            ),
            "location": forms.TextInput(attrs={"list": "campus-locations", "placeholder": "e.g. Central Library"}),
            "date_lost_found": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "contact_method": forms.TextInput(attrs={"placeholder": "e.g. Email me at name@nitc.ac.in"}),
            "collection_point": forms.TextInput(attrs={"placeholder": "e.g. Security office, Main Building"}),
            "photo": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [("", "Select a category")] + CATEGORY_CHOICES
        self.fields["date_lost_found"].widget.attrs["max"] = timezone.localdate().isoformat()
        for name, field in self.fields.items():
            if name == "report_type":
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()
        self.fields["photo"].widget.attrs["data-max-bytes"] = settings.LOSTFOUND_MAX_PHOTO_SIZE

    # ---- Field validation --------------------------------------------------
    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        return title

    def clean_date_lost_found(self):
        value = self.cleaned_data["date_lost_found"]
        if value and value > timezone.localdate():
            raise forms.ValidationError("The date cannot be in the future.")
        return value

    def clean_photo(self):
        """FR-09: size (<= 5 MB) and content type (JPEG / PNG / WebP) checks."""
        photo = self.cleaned_data.get("photo")
        # Only validate newly uploaded files (existing files have no content_type).
        if not photo or not hasattr(photo, "content_type"):
            return photo

        max_size = settings.LOSTFOUND_MAX_PHOTO_SIZE
        if photo.size > max_size:
            raise forms.ValidationError(
                f"The photo is too large ({filesizeformat(photo.size)}). "
                f"The maximum allowed size is {filesizeformat(max_size)}."
            )

        content_type = (photo.content_type or "").lower()
        if content_type not in settings.LOSTFOUND_ALLOWED_PHOTO_TYPES:
            raise forms.ValidationError("Unsupported photo type. Please upload a JPEG, PNG or WebP image.")
        return photo


class ItemFilterForm(forms.Form):
    """GET form for keyword search (FR-13) and filters (FR-14, FR-15)."""

    q = forms.CharField(
        required=False,
        label="Keyword",
        widget=forms.TextInput(attrs={"placeholder": "Search title, description, location, category...", "type": "search"}),
    )
    type = forms.ChoiceField(
        required=False, label="Report type", choices=[("", "All types")] + list(ReportType.choices)
    )
    category = forms.ChoiceField(required=False, choices=[("", "All categories")] + CATEGORY_CHOICES)
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"list": "campus-locations", "placeholder": "Any location"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()

    @staticmethod
    def campus_locations():
        return CAMPUS_LOCATIONS
