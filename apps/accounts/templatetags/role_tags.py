from django import template

register = template.Library()


@register.filter
def has_role(user, roles):

    if not user.is_authenticated:
        return False

    roles_list = roles.split(",")

    if user.is_superuser:
        return True

    return user.role in roles_list


@register.filter
def peut_ecrire(user):
    """Vrai pour les rôles opérationnels. La direction (ADMIN, GÉRANT,
    superuser) est en lecture seule : on lui masque les boutons d'action."""

    if not user.is_authenticated:
        return False

    if user.is_superuser or user.role in ("ADMIN", "GERANT"):
        return False

    return user.role in ("CAISSIER", "SERVEUR", "CUISINIER", "VENDEUR", "LIVREUR")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)