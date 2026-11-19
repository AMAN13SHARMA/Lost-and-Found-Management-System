"""WSGI config for the Lost and Found Management System."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lostfound.settings")

application = get_wsgi_application()

# On Vercel serverless cold start, initialize /tmp/db.sqlite3 with migrations & NITC demo data.
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    from django.core.management import call_command
    from django.db import connection

    if "auth_user" not in connection.introspection.table_names():
        call_command("migrate", interactive=False, verbosity=0)
        call_command("seed_demo", verbosity=0)

# Alias `app` for WSGI runners that look for `app`.
app = application
