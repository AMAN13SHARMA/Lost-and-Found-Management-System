"""ASGI config for the Lost and Found Management System."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lostfound.settings")

application = get_asgi_application()
