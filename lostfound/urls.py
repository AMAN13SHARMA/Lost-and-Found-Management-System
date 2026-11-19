"""Root URL configuration for the Lost and Found Management System."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.urls import include, path, re_path
from django.views.static import serve

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

# Serve uploaded photos and static assets in local development and on Vercel demo deployments.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "IS_VERCEL", False):
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        re_path(r"^static/(?P<path>.*)$", staticfiles_serve, {"insecure": True}),
    ]

handler403 = "items.views.permission_denied_view"
handler404 = "items.views.page_not_found_view"
