"""
Class Diagram 2 - Lost and Found Item Management.

Item            - a LOST or FOUND report (FR-06 .. FR-11, FR-31, FR-33)
ReportType      - <<enumeration>> LOST, FOUND (FR-06, FR-14)
ItemStatus      - <<enumeration>> OPEN, CLAIM_PENDING, RESOLVED (FR-10, FR-21, FR-31)

State machine (SRS Figure B.3):
    [new] -> OPEN --(claim submitted)--> CLAIM_PENDING
    OPEN / CLAIM_PENDING --(creator or staff marks resolved)--> RESOLVED
    Claim approval / rejection does NOT resolve the item (BR-06).
"""
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


class ReportType(models.TextChoices):
    LOST = "LOST", "Lost"
    FOUND = "FOUND", "Found"


class ItemStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLAIM_PENDING = "CLAIM_PENDING", "Claim pending"
    RESOLVED = "RESOLVED", "Resolved"


# Categories are stored as readable words so that the case-insensitive
# keyword search over "category" (FR-13) matches what users type.
CATEGORY_CHOICES = [
    ("ID Card", "ID Card"),
    ("Electronics", "Electronics"),
    ("Mobile Phone", "Mobile Phone"),
    ("Laptop & Accessories", "Laptop & Accessories"),
    ("Books & Notes", "Books & Notes"),
    ("Stationery", "Stationery"),
    ("Keys", "Keys"),
    ("Wallet & Purse", "Wallet & Purse"),
    ("Bags", "Bags"),
    ("Clothing", "Clothing"),
    ("Accessories", "Accessories"),
    ("Jewellery", "Jewellery"),
    ("Documents", "Documents"),
    ("Water Bottle", "Water Bottle"),
    ("Sports Equipment", "Sports Equipment"),
    ("Others", "Others"),
]

CATEGORY_ICONS = {
    "ID Card": "🪪",
    "Electronics": "🔌",
    "Mobile Phone": "📱",
    "Laptop & Accessories": "💻",
    "Books & Notes": "📚",
    "Stationery": "✏️",
    "Keys": "🔑",
    "Wallet & Purse": "👛",
    "Bags": "🎒",
    "Clothing": "🧥",
    "Accessories": "⌚",
    "Jewellery": "💍",
    "Documents": "📄",
    "Water Bottle": "🧴",
    "Sports Equipment": "🏸",
    "Others": "📦",
}

# Suggestions shown in the location field (free text is still allowed).
CAMPUS_LOCATIONS = [
    "Central Library",
    "Main Building",
    "Electrical Lecture Hall Complex (ELHC)",
    "New Lecture Hall Complex (NLHC)",
    "Central Computer Centre (CCC)",
    "Aryabhatta Hall",
    "Main Canteen",
    "Mini Canteen",
    "Mega Boys Hostel (MBH)",
    "Ladies Hostel (LH)",
    "Indoor Stadium",
    "Sports Ground",
    "Health Centre",
    "Co-operative Store",
    "Main Gate",
    "Bus Stop",
    "Department of CSE",
    "Department of ECE",
    "Department of EEE",
    "Department of ME",
    "Department of CE",
    "Department of Chemical Engineering",
    "Department of Architecture",
    "School of Management Studies (SOMS)",
]


class ItemQuerySet(models.QuerySet):
    def unresolved(self):
        """FR-12, FR-32, BR-07: everything that is not RESOLVED."""
        return self.exclude(status=ItemStatus.RESOLVED)

    def owned_by(self, user):
        return self.filter(created_by=user)


class Item(models.Model):
    title = models.CharField(max_length=120)
    report_type = models.CharField(
        "report type", max_length=5, choices=ReportType.choices, default=ReportType.LOST, db_index=True
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField(
        help_text="Describe the item (colour, brand, marks). Avoid sensitive identifiers such as full ID numbers."
    )
    photo = models.ImageField(
        upload_to="item_photos/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
        help_text="Optional. JPEG, PNG or WebP, maximum 5 MB.",
    )
    location = models.CharField(max_length=150, help_text="Where the item was lost or found.")
    date_lost_found = models.DateField("date lost / found")
    collection_point = models.CharField(
        "collection point",
        max_length=150,
        blank=True,
        help_text="Optional. Where a found item can be collected (e.g. Security office, Main Building).",
    )
    contact_method = models.CharField(
        "contact method",
        max_length=150,
        help_text="How others can reach you (e.g. email, phone, hostel room).",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items", verbose_name="creator"
    )
    status = models.CharField(max_length=15, choices=ItemStatus.choices, default=ItemStatus.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)  # FR-11
    updated_at = models.DateTimeField(auto_now=True)      # FR-11, FR-33

    objects = ItemQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "item report"
        verbose_name_plural = "item reports"

    def __str__(self):
        return f"[{self.get_report_type_display()}] {self.title}"

    def get_absolute_url(self):
        return reverse("items:item_detail", args=[self.pk])

    # ---- Methods from Class Diagram 2 --------------------------------------
    def mark_resolved(self) -> None:
        """FR-31 / FR-33: set RESOLVED and refresh the modification timestamp."""
        self.status = ItemStatus.RESOLVED
        self.save(update_fields=["status", "updated_at"])

    def mark_claim_pending(self) -> None:
        """FR-21: a newly submitted claim moves an OPEN item to CLAIM_PENDING."""
        if self.status != ItemStatus.RESOLVED and self.status != ItemStatus.CLAIM_PENDING:
            self.status = ItemStatus.CLAIM_PENDING
            self.save(update_fields=["status", "updated_at"])

    def is_resolved(self) -> bool:
        return self.status == ItemStatus.RESOLVED

    def is_owned_by(self, user) -> bool:
        return bool(user and user.is_authenticated and self.created_by_id == user.pk)

    # ---- Presentation helpers ----------------------------------------------
    @property
    def is_lost(self):
        return self.report_type == ReportType.LOST

    @property
    def is_found(self):
        return self.report_type == ReportType.FOUND

    @property
    def category_icon(self):
        return CATEGORY_ICONS.get(self.category, "📦")

    @property
    def status_css(self):
        return {
            ItemStatus.OPEN: "open",
            ItemStatus.CLAIM_PENDING: "pending",
            ItemStatus.RESOLVED: "resolved",
        }.get(self.status, "open")
