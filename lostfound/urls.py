"""Root URL configuration for the Lost and Found Management System."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "NITC Lost & Found - Administration"
admin.site.site_title = "NITC Lost & Found Admin"
admin.site.index_title = "Manage users, item reports and claim requests"

urlpatterns = [
    path("admin/", admin.site.urls),                     # FR-34, FR-35
    path("accounts/", include("accounts.urls")),          # FR-01..FR-05
    path("dashboard/", include("dashboard.urls")),        # FR-27..FR-29
    path("claims/", include("claims.urls")),              # FR-17..FR-26
    path("", include("items.urls")),                      # FR-06..FR-16, FR-30..FR-33
]

# Serve uploaded photos during local development only (SRS 2.4 server env).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "items.views.permission_denied_view"
handler404 = "items.views.page_not_found_view"
