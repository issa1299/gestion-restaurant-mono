"""
Settings de production pour PythonAnywhere.
Utilisé via : DJANGO_SETTINGS_MODULE=config.settings_prod
"""

import os
from .settings import *  # noqa: F401,F403

DEBUG = False

# SECRET_KEY doit être fourni par l'environnement en production.
# Sur PythonAnywhere, ajoutez-le dans l'onglet "Web" > "Environment variables"
# (ou définissez-le en tête du WSGI). Ne JAMAIS le laisser en dur ici.
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY manquant : définissez la variable d'environnement SECRET_KEY.")

# Domaine pythonanywhere : <utilisateur>.pythonanywhere.com
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "issa72.pythonanywhere.com,www.issa72.pythonanywhere.com",
).split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.pythonanywhere.com",
).split(",")

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

# Sécurité HTTP (PythonAnywhere termine le TLS à son niveau de proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
