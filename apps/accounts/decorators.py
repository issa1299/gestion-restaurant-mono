from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


# Accueil accessible selon le rôle (évite les boucles de redirection)
ROLE_HOME = {
    "CLIENT": "menu:accueil",
    "VENDEUR": "menu:gestion",
    "LIVREUR": "livraison:liste",
    "GERANT": "dashboard:index",
    "ADMIN": "dashboard:index",
}


# Rôles de direction : consultation uniquement sauf mention contraire
ROLES_SUPERVISION = ("ADMIN", "GERANT")


def role_required(allowed_roles=[], ecriture_autorisee=False):
    """
    Restreint une vue à certains rôles.

    Les rôles de direction (ADMIN, GÉRANT) et les superusers
    sont en LECTURE SEULE : toute requête de modification
    (POST/PUT/PATCH/DELETE) est bloquée, sauf si la vue
    est explicitement marquée `ecriture_autorisee=True`
    (gestion des utilisateurs, paramètres du restaurant).
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("accounts:login")

            est_direction = (
                request.user.is_superuser
                or request.user.role in ROLES_SUPERVISION
            )

            # Accès à la vue
            if request.user.is_superuser or request.user.role in allowed_roles:
                # Lecture seule pour la direction (sauf écriture autorisée)
                if (
                    not ecriture_autorisee
                    and est_direction
                    and request.method not in ("GET", "HEAD", "OPTIONS")
                ):
                    messages.error(
                        request,
                        "Votre rôle est en lecture seule : "
                        "cette action de modification est interdite."
                    )
                    return redirect(
                        request.META.get("HTTP_REFERER")
                        or ROLE_HOME.get(request.user.role, "dashboard:index")
                    )

                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            messages.error(
                request,
                "Accès refusé : vous n'avez pas la permission."
            )

            return redirect(ROLE_HOME.get(request.user.role, "dashboard:index"))

        return wrapper

    return decorator