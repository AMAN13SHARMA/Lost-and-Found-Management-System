"""
ClaimViews (Class Diagram 3, Sequence Diagram 2).

+submit_claim_view(request, item_id)          FR-17 .. FR-22, BR-01 .. BR-03
+decide_claim_view(request, claim_id, action) FR-23 .. FR-26, BR-04, BR-05
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from items.models import Item

from .forms import ClaimForm
from .models import ClaimAlreadyReviewed, ClaimRequest
from .services import can_decide, check_eligibility, claim_ineligibility_reason  # noqa: F401


def _redirect_back(request, fallback):
    nxt = request.POST.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect(fallback)


@login_required
@require_POST
def submit_claim_view(request, item_id):
    """Sequence Diagram 2, part A - Submit a claim."""
    item = get_object_or_404(Item, pk=item_id)

    # Steps 3-6: eligibility checks (resolved / own item / duplicate).
    reason = claim_ineligibility_reason(request.user, item)
    if reason:
        messages.error(request, reason)
        return redirect(item)

    form = ClaimForm(request.POST)
    if not form.is_valid():
        # UI-01 / FR-17: show the validation error on the item page.
        for error in form.errors.get("message", []):
            messages.error(request, error)
        request.session["claim_draft"] = {"item": item.pk, "message": request.POST.get("message", "")}
        return redirect(f"{item.get_absolute_url()}#claim")

    try:
        with transaction.atomic():
            # Step 7: store claim, claimStatus = PENDING (FR-21)
            form.save(item=item, claimant=request.user)
            # Steps 8-9: itemStatus = CLAIM_PENDING (FR-21)
            item.mark_claim_pending()
    except IntegrityError:
        # NFR-15: database uniqueness constraint (race-condition safety net).
        messages.error(request, "You have already submitted a claim for this item.")
        return redirect(item)

    request.session.pop("claim_draft", None)
    # Steps 10-11 / FR-22: on-page confirmation.
    messages.success(
        request,
        "Your claim request has been submitted and is now PENDING. "
        "The report creator will review your explanation.",
    )
    return redirect(item)


@login_required
@require_POST
def decide_claim_view(request, claim_id, action):
    """Sequence Diagram 2, part B - Review the claim."""
    claim = get_object_or_404(ClaimRequest.objects.select_related("item", "claimant"), pk=claim_id)
    fallback = claim.item.get_absolute_url()

    if action not in ("approve", "reject"):
        messages.error(request, "Unknown claim action.")
        return _redirect_back(request, fallback)

    # FR-23 / BR-05 / NFR-08: only the creator or authorized staff.
    if not can_decide(request.user, claim):
        messages.error(request, "You do not have permission to review this claim.")
        return _redirect_back(request, fallback)

    # Steps 13-14 / FR-25 / BR-04: only pending claims can be decided.
    if not claim.is_pending():
        messages.warning(
            request, f"This claim has already been reviewed ({claim.get_status_display()}) and cannot be changed."
        )
        return _redirect_back(request, fallback)

    try:
        with transaction.atomic():
            # Re-read the row inside the transaction so a concurrent decision
            # cannot be overwritten (approve()/reject() re-check is_pending()).
            fresh = ClaimRequest.objects.select_for_update().get(pk=claim.pk)
            if action == "approve":
                fresh.approve()   # steps 15-16
            else:
                fresh.reject()    # steps 17-18
    except ClaimAlreadyReviewed:
        messages.warning(request, "This claim has already been reviewed and cannot be changed.")
        return _redirect_back(request, fallback)

    # Step 19 / FR-26: show the updated claim status.
    if action == "approve":
        messages.success(
            request,
            f"Claim by {claim.claimant.username} is now APPROVED. Please arrange the physical handover at a safe "
            "campus location, then mark the report as resolved. Approval is not automatic proof of ownership.",
        )
    else:
        messages.info(request, f"Claim by {claim.claimant.username} is now REJECTED.")
    return _redirect_back(request, fallback)
