"""
Eligibility and permission rules used by ClaimViews (Class Diagram 3).

+check_eligibility(user, item) : bool
+can_decide(user, claim)       : bool

Business rules enforced:
BR-01 / FR-04 - user must be logged in to submit a claim
BR-02 / FR-18 - a user cannot claim their own report
FR-19         - no claims on RESOLVED reports
BR-03 / FR-20 - one claim per claimant per item
BR-04 / FR-25 - only PENDING claims can be decided
BR-05 / FR-23 - only the item creator or authorized staff can decide
"""
from django.conf import settings

from accounts.models import is_authorized_staff
from items.models import ReportType

from .models import ClaimRequest


def claim_ineligibility_reason(user, item):
    """Return a human-readable reason why ``user`` cannot claim ``item``, or None."""
    if not (user and user.is_authenticated):
        return "You must be logged in to submit a claim."
    if item.is_owned_by(user):
        return "You cannot submit a claim for your own report."
    if item.is_resolved():
        return "This report has already been resolved, so it can no longer be claimed."
    if getattr(settings, "LOSTFOUND_RESTRICT_CLAIMS_TO_FOUND", False) and item.report_type != ReportType.FOUND:
        return "Claims can only be submitted for FOUND item reports."
    if ClaimRequest.objects.filter(item=item, claimant=user).exists():
        return "You have already submitted a claim for this item."
    return None


def check_eligibility(user, item) -> bool:
    return claim_ineligibility_reason(user, item) is None


def can_decide(user, claim) -> bool:
    """FR-23 / BR-05 / NFR-08: item creator or authorized staff."""
    if not (user and user.is_authenticated):
        return False
    return claim.item.is_owned_by(user) or is_authorized_staff(user)


def can_manage_item(user, item) -> bool:
    """FR-31 / BR-05: item creator or authorized staff may resolve a report."""
    if not (user and user.is_authenticated):
        return False
    return item.is_owned_by(user) or is_authorized_staff(user)
