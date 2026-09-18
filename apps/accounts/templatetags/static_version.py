"""Templatetags de versionnement des fichiers statiques.

`static_version` retourne l'URL d'un fichier statique suffixée par un
paramètre ?v=<mtime du fichier>. Dès que le fichier est modifié, l'URL
change et le cache navigateur est automatiquement invalidé — plus besoin
de Ctrl+F5 après chaque modification de JS/CSS.
"""
import os

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders

register = template.Library()


def _url_statique(chemin):
    """Réutilise exactement la mécanique du tag {% static %} de Django."""
    try:
        from django.templatetags.static import StaticNode
        return StaticNode.handle_simple(chemin)
    except Exception:
        return settings.STATIC_URL + chemin


@register.simple_tag
def static_version(chemin):
    url = _url_statique(chemin)
    try:
        chemin_fichier = finders.find(chemin)
        if chemin_fichier and os.path.exists(chemin_fichier):
            version = int(os.path.getmtime(chemin_fichier))
            separateur = "&" if "?" in url else "?"
            return f"{url}{separateur}v={version}"
    except Exception:
        pass
    return url