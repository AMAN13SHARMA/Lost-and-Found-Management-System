"""Values available to every template."""
from django.conf import settings

from .models import CAMPUS_LOCATIONS


def site_context(request):
    return {
        "SITE_NAME": "NITC Lost & Found",
        "CAMPUS_LOCATIONS": CAMPUS_LOCATIONS,
        "MAX_PHOTO_MB": settings.LOSTFOUND_MAX_PHOTO_SIZE // (1024 * 1024),
    }
