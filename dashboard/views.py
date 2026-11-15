"""Personal dashboard view (SRS 4.7, FR-27 .. FR-29; FR-04 login required)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from claims.models import ClaimRequest
from items.models import Item

from .services import DashboardService


@login_required
def dashboard_view(request):
    user = request.user
    context = {
        "summary": DashboardService.show_summary(user),
        "breakdown": DashboardService.report_status_breakdown(user),
        "received_claims": DashboardService.get_received_claims(user)[:10],
        "recent_reports": Item.objects.filter(created_by=user).order_by("-created_at")[:5],
        "recent_claims": ClaimRequest.objects.filter(claimant=user).select_related("item").order_by("-created_at")[:5],
    }
    return render(request, "dashboard/dashboard.html", context)
