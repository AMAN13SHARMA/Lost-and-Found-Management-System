"""Django Admin for item reports (FR-34: view, edit or delete item reports)."""
from django.contrib import admin
from django.utils.html import format_html

from claims.models import ClaimRequest

from .models import Item, ItemStatus


class ClaimRequestInline(admin.TabularInline):
    model = ClaimRequest
    extra = 0
    fields = ("claimant", "message", "status", "created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("claimant",)
    show_change_link = True


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "report_type", "category", "location", "status", "created_by", "created_at", "thumb")
    list_filter = ("report_type", "status", "category", "created_at")
    search_fields = ("title", "description", "location", "category", "created_by__username")
    list_select_related = ("created_by",)
    readonly_fields = ("created_at", "updated_at", "preview")
    raw_id_fields = ("created_by",)
    date_hierarchy = "created_at"
    inlines = [ClaimRequestInline]
    actions = ["mark_selected_resolved"]
    fieldsets = (
        ("Report", {"fields": ("report_type", "title", "category", "description")}),
        ("Where & when", {"fields": ("location", "date_lost_found", "collection_point", "contact_method")}),
        ("Photo", {"fields": ("photo", "preview")}),
        ("Status", {"fields": ("status", "created_by", "created_at", "updated_at")}),
    )

    @admin.display(description="Photo")
    def thumb(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="height:36px;border-radius:4px">', obj.photo.url)
        return "-"

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height:240px;border-radius:6px">', obj.photo.url)
        return "No photo uploaded"

    @admin.action(description="Mark selected reports as RESOLVED")
    def mark_selected_resolved(self, request, queryset):
        count = 0
        for item in queryset.exclude(status=ItemStatus.RESOLVED):
            item.mark_resolved()  # keeps updated_at current (FR-33)
            count += 1
        self.message_user(request, f"{count} report(s) marked as resolved.")
