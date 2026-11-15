"""
Class Diagram 3 - Claim Request Management.

ClaimRequest  - a claim on an item with message, status and timestamp
                (FR-17, FR-21, FR-24). Unique on (item, claimant) - NFR-15, BR-03.
ClaimStatus   - <<enumeration>> PENDING, APPROVED, REJECTED (FR-21, FR-24, BR-04)

State machine (SRS Figure B.4):
    [new] -> PENDING --approve()--> APPROVED
                     --reject()---> REJECTED
    A reviewed claim cannot be decided again (FR-25, BR-04).
"""
from django.conf import settings
from django.db import models


class ClaimStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ClaimAlreadyReviewed(Exception):
    """Raised when approve()/reject() is called on a non-pending claim (FR-25)."""


class ClaimRequest(models.Model):
    item = models.ForeignKey("items.Item", on_delete=models.CASCADE, related_name="claims")
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="claims_submitted"
    )
    message = models.TextField(
        "ownership explanation",
        help_text="Explain why this item belongs to you (identifying marks, contents, where/when you lost it).",
    )
    status = models.CharField(max_length=10, choices=ClaimStatus.choices, default=ClaimStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "claim request"
        verbose_name_plural = "claim requests"
        constraints = [
            # NFR-15 / BR-03 / FR-20: one claim per claimant per item.
            models.UniqueConstraint(fields=["item", "claimant"], name="unique_claim_per_item_and_claimant"),
        ]

    def __str__(self):
        return f"Claim by {self.claimant} on '{self.item.title}' ({self.get_status_display()})"

    # ---- Methods from Class Diagram 3 --------------------------------------
    def is_pending(self) -> bool:
        return self.status == ClaimStatus.PENDING

    def approve(self) -> None:
        """FR-24. Approval does NOT resolve the item (BR-06, NFR-05)."""
        if not self.is_pending():
            raise ClaimAlreadyReviewed("Only pending claims can be approved.")
        self.status = ClaimStatus.APPROVED
        self.save(update_fields=["status"])

    def reject(self) -> None:
        """FR-24."""
        if not self.is_pending():
            raise ClaimAlreadyReviewed("Only pending claims can be rejected.")
        self.status = ClaimStatus.REJECTED
        self.save(update_fields=["status"])

    def is_duplicate(self) -> bool:
        """True if another claim already exists for the same (item, claimant)."""
        qs = ClaimRequest.objects.filter(item_id=self.item_id, claimant_id=self.claimant_id)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs.exists()

    @property
    def status_css(self):
        return {
            ClaimStatus.PENDING: "pending",
            ClaimStatus.APPROVED: "approved",
            ClaimStatus.REJECTED: "rejected",
        }.get(self.status, "pending")
