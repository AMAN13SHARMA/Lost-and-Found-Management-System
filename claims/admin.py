"""Django Admin for claim requests (FR-34: view, edit or delete claims)."""
from django.contrib import admin

from .models import ClaimRequest, ClaimStatus


@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "claimant", "status", "created_at")
    list_filter = ("status", "item__report_type", "created_at")
    search_fields = ("item__title", "claimant__username", "claimant__email", "message")
    list_select_related = ("item", "claimant")
    raw_id_fields = ("item", "claimant")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected pending claims")
    def approve_selected(self, request, queryset):
        updated = queryset.filter(status=ClaimStatus.PENDING).update(status=ClaimStatus.APPROVED)
        self.message_user(request, f"{updated} pending claim(s) approved.")

    @admin.action(description="Reject selected pending claims")
    def reject_selected(self, request, queryset):
        updated = queryset.filter(status=ClaimStatus.PENDING).update(status=ClaimStatus.REJECTED)
        self.message_user(request, f"{updated} pending claim(s) rejected.")
