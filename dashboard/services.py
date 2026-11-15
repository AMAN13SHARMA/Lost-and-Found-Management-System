"""
DashboardService (Class Diagram 3, Sequence Diagram 3).

The dashboard is computed from the user's own records and is not stored.

+count_user_reports(user)    : int       FR-27
+count_pending_claims(user)  : int       FR-28
+count_submitted_claims(user): int       FR-29
+get_received_claims(user)   : QuerySet  (claims received on the user's reports)
"""
from django.db.models import Case, IntegerField, When

from claims.models import ClaimRequest, ClaimStatus
from items.models import Item, ItemStatus


class DashboardService:
    @staticmethod
    def count_user_reports(user) -> int:
        """FR-27: total item reports created by the user."""
        return Item.objects.filter(created_by=user).count()

    @staticmethod
    def count_pending_claims(user) -> int:
        """FR-28: pending claims on reports created by the user."""
        return ClaimRequest.objects.filter(item__created_by=user, status=ClaimStatus.PENDING).count()

    @staticmethod
    def count_submitted_claims(user) -> int:
        """FR-29: claim requests submitted by the user."""
        return ClaimRequest.objects.filter(claimant=user).count()

    @staticmethod
    def get_received_claims(user):
        """Claims received on the user's reports, pending first."""
        return (
            ClaimRequest.objects.filter(item__created_by=user)
            .select_related("item", "claimant")
            .annotate(
                pending_first=Case(
                    When(status=ClaimStatus.PENDING, then=0), default=1, output_field=IntegerField()
                )
            )
            .order_by("pending_first", "-created_at")
        )

    # ---- Sequence Diagram 3 helpers ----------------------------------------
    @classmethod
    def show_summary(cls, user) -> dict:
        """Dashboard.showSummary(): the three counts (steps 4-11)."""
        return {
            "total_reports": cls.count_user_reports(user),
            "pending_claims_received": cls.count_pending_claims(user),
            "claims_submitted": cls.count_submitted_claims(user),
        }

    @staticmethod
    def report_status_breakdown(user) -> dict:
        qs = Item.objects.filter(created_by=user)
        return {
            "open": qs.filter(status=ItemStatus.OPEN).count(),
            "claim_pending": qs.filter(status=ItemStatus.CLAIM_PENDING).count(),
            "resolved": qs.filter(status=ItemStatus.RESOLVED).count(),
        }
