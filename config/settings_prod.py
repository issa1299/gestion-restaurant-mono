"""
Settings de production pour PythonAnywhere.
Utilisé via : DJANGO_SETTINGS_MODULE=config.settings_prod
"""

import os
from .settings import *  # noqa: F401,F403

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)

# Domaine pythonanywhere : <utilisateur>.pythonanywhere.com
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["https://*.pythonanywhere.com"]

# Le plan gratuit de PythonAnywhere n'expose pas de WebSockets.
# Channels reste installé mais l'app tourne en WSGI ; les notifications
# temps réel sont silencieusement ignorées (try/except dans utils.py).

# SQLite est utilisé pour ce test (stockage sur le serveur PythonAnywhere).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
