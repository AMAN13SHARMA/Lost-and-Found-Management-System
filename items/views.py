"""
ItemViews (Class Diagram 2, Sequence Diagram 1).

+home_view(request)                           UI Home Page, FR-32
+item_list_view(request)                      FR-12 .. FR-15
+item_detail_view(request, item_id)           FR-16, UI-03
+create_item_view(request)                    FR-06 .. FR-11
+mark_resolved_view(request, item_id)         FR-31 .. FR-33
+my_items_view(request)                       FR-30
+search_items(keyword, type, category, location) : QuerySet   FR-13 .. FR-15
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from claims.forms import ClaimForm
from claims.models import ClaimRequest, ClaimStatus
from claims.services import can_manage_item, claim_ineligibility_reason

from .forms import ItemFilterForm, ItemForm
from .models import Item, ItemStatus, ReportType


def search_items(keyword="", type="", category="", location="", queryset=None):  # noqa: A002 - name from class diagram
    """
    Case-insensitive keyword search over title, description, location and
    category (FR-13) plus optional report-type / category / location filters
    (FR-14, FR-15). Resolved reports are excluded (FR-12, FR-32, BR-07).
    """
    qs = (queryset if queryset is not None else Item.objects.all()).unresolved()

    keyword = (keyword or "").strip()
    if keyword:
        qs = qs.filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(location__icontains=keyword)
            | Q(category__icontains=keyword)
        )
    if type in ReportType.values:
        qs = qs.filter(report_type=type)               # filterByType()
    if category:
        qs = qs.filter(category=category)              # filterByCategory()
    location = (location or "").strip()
    if location:
        qs = qs.filter(location__icontains=location)   # filterByLocation()
    return qs.select_related("created_by")


def home_view(request):
    """Recent unresolved reports + navigation (SRS 3.1 Home Page, FR-32)."""
    recent = Item.objects.unresolved().select_related("created_by")[: settings.LOSTFOUND_RECENT_ON_HOME]
    stats = Item.objects.aggregate(
        lost=Count("id", filter=Q(report_type=ReportType.LOST) & ~Q(status=ItemStatus.RESOLVED)),
        found=Count("id", filter=Q(report_type=ReportType.FOUND) & ~Q(status=ItemStatus.RESOLVED)),
        resolved=Count("id", filter=Q(status=ItemStatus.RESOLVED)),
    )
    return render(request, "items/home.html", {"recent_items": recent, "stats": stats})


def item_list_view(request):
    """Item Listing Page with search and filters (FR-12 .. FR-15). GET only (SRS 3.4)."""
    form = ItemFilterForm(request.GET or None)
    params = {"keyword": "", "type": "", "category": "", "location": ""}
    if form.is_bound and form.is_valid():
        params = {
            "keyword": form.cleaned_data.get("q", ""),
            "type": form.cleaned_data.get("type", ""),
            "category": form.cleaned_data.get("category", ""),
            "location": form.cleaned_data.get("location", ""),
        }
    results = search_items(**params)

    paginator = Paginator(results, settings.LOSTFOUND_ITEMS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    is_filtered = any(params.values())
    return render(
        request,
        "items/item_list.html",
        {
            "form": form,
            "page_obj": page_obj,
            "items": page_obj.object_list,
            "total": paginator.count,
            "is_filtered": is_filtered,
        },
    )


def item_detail_view(request, item_id):
    """Item Detail Page (FR-16) with claim / review / resolve actions (UI-03)."""
    item = get_object_or_404(Item.objects.select_related("created_by"), pk=item_id)
    user = request.user

    can_manage = can_manage_item(user, item)
    context = {
        "item": item,
        "can_manage": can_manage,
        "is_owner": item.is_owned_by(user),
        "claims": None,
        "claim_form": None,
        "claim_block_reason": None,
        "user_claim": None,
    }

    if can_manage:
        # Pending claims first, then newest.
        context["claims"] = (
            item.claims.select_related("claimant")
            .annotate(pending_first=Case(When(status=ClaimStatus.PENDING, then=0), default=1, output_field=IntegerField()))
            .order_by("pending_first", "-created_at")
        )
        context["pending_count"] = item.claims.filter(status=ClaimStatus.PENDING).count()

    if user.is_authenticated:
        context["user_claim"] = ClaimRequest.objects.filter(item=item, claimant=user).first()
        reason = claim_ineligibility_reason(user, item)
        if reason is None:
            draft = request.session.get("claim_draft") or {}
            initial = {"message": draft.get("message", "")} if draft.get("item") == item.pk else {}
            context["claim_form"] = ClaimForm(initial=initial)
        elif not item.is_owned_by(user):
            context["claim_block_reason"] = reason

    return render(request, "items/item_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def create_item_view(request):
    """Report Form (FR-06 .. FR-11). Photos are sent as multipart/form-data."""
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user      # FR-10 associate with creator
            item.status = ItemStatus.OPEN        # FR-10 initial status OPEN
            item.save()                          # FR-11 timestamps set automatically
            messages.success(
                request, f"Your {item.get_report_type_display().lower()} item report \u201c{item.title}\u201d was created."
            )
            return redirect(item)
        # UI-01 / FR-05: nothing is saved, errors are displayed.
        messages.error(request, "The report could not be saved. Please correct the errors below.")
    else:
        initial = {}
        if request.GET.get("type") in ReportType.values:
            initial["report_type"] = request.GET["type"]
        form = ItemForm(initial=initial)
    return render(request, "items/item_form.html", {"form": form, "locations": ItemFilterForm.campus_locations()})


@login_required
@require_POST
def mark_resolved_view(request, item_id):
    """FR-31 / FR-33 / BR-05 / NFR-08 - Sequence Diagram 2 part C."""
    item = get_object_or_404(Item, pk=item_id)
    if not can_manage_item(request.user, item):
        messages.error(request, "Only the report creator or authorized staff can mark this report as resolved.")
        return redirect(item)
    if item.is_resolved():
        messages.info(request, "This report is already marked as resolved.")
        return redirect(item)

    item.mark_resolved()
    messages.success(
        request, f"\u201c{item.title}\u201d has been marked as RESOLVED and is no longer shown in the public listing."
    )
    return redirect(item)


@login_required
def my_items_view(request):
    """My Items Page (FR-30): own reports (all statuses) + submitted claims."""
    my_items = (
        Item.objects.owned_by(request.user)
        .annotate(
            claim_total=Count("claims"),
            claim_pending=Count("claims", filter=Q(claims__status=ClaimStatus.PENDING)),
        )
        .order_by("-created_at")
    )
    my_claims = (
        ClaimRequest.objects.filter(claimant=request.user)
        .select_related("item", "item__created_by")
        .order_by("-created_at")
    )
    tab = request.GET.get("tab", "reports")
    return render(
        request,
        "items/my_items.html",
        {"my_items": my_items, "my_claims": my_claims, "tab": tab if tab in ("reports", "claims") else "reports"},
    )


# ---------------------------------------------------------------------------
# Friendly error pages
# ---------------------------------------------------------------------------
def permission_denied_view(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found_view(request, exception=None):
    return render(request, "errors/404.html", status=404)
