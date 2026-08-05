# ============================================================
# FICHIER WSGI POUR PYTHONANYWHERE
# À copier-coller dans l'onglet "Web" > "WSGI configuration file"
# Remplacez VOTRE_UTILISATEUR par votre nom PythonAnywhere.
# ============================================================

import os
import sys

# Chemin vers le dossier du projet (monter par le dossier "Files")
PROJET = '/home/VOTRE_UTILISATEUR/RestaurantPro-Mono'
sys.path.insert(0, PROJET)
sys.path.insert(0, os.path.join(PROJET, 'config'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_prod'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
