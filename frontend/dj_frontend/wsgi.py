"""WSGI config for dj_frontend project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_frontend.settings")
application = get_wsgi_application()
