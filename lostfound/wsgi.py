"""WSGI config for the Lost and Found Management System."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lostfound.settings")

application = get_wsgi_application()
