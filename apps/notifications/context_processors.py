from django.core.cache import cache

from apps.commandes.models import Commande

CACHE_DUREE = 15


def navbar_notifications(request):
    """
    Context processor qui fournit les données réelles pour la navbar :
    - Dernières commandes en attente / en préparation
    - Nombre de notifications non lues
    """
    context = {}

    if request.user.is_authenticated:
        donnees = cache.get("navbar_notifications")
        if donnees is None:
            # === Dernières commandes récentes ===
            commandes_recentes = Commande.objects.filter(
                statut__in=["EN_ATTENTE", "EN_PREPARATION", "PRETE"]
            ).select_related("client", "table").order_by("-created_at")[:5]

            # === Stats pour les badges ===
            nb_commandes_en_attente = Commande.objects.filter(
                statut__in=["EN_ATTENTE", "EN_PREPARATION"]
            ).count()

            # Nombre total de notifications (commandes récentes)
            nb_notifications = min(nb_commandes_en_attente, 5)

            # === Messages (représentés par les commandes prêtes qui attendent) ===
            commandes_pretes = Commande.objects.filter(
                statut="PRETE"
            ).select_related("client", "table").order_by("-created_at")[:3]
            nb_messages = commandes_pretes.count()

            # Assembler les notifications de commandes
            notifications_commandes = []
            for cmd in commandes_recentes:
                client_nom = cmd.client.nom if cmd.client else "Client"
                if cmd.type == "LIVRAISON":
                    table_info = "Livraison"
                elif cmd.table:
                    table_info = f"Table {cmd.table.numero}"
                else:
                    table_info = "Sur place"
                notifications_commandes.append({
                    "id": cmd.id,
                    "client": client_nom,
                    "table": table_info,
                    "statut": cmd.statut,
                    "icone": "utensils",
                    "couleur_icone": "blue",
                    "message": f"Commande N° {cmd.id} - {table_info}",
                })

            # Notifications : commandes récentes
            notifications_list = notifications_commandes[:8]

            donnees = {
                "notifications_list": notifications_list,
                "nb_notifications": nb_notifications,
                "commandes_pretes_list": list(commandes_pretes),
                "nb_messages": nb_messages,
            }
            cache.set("navbar_notifications", donnees, CACHE_DUREE)

        context.update({
            "notifications_list": donnees["notifications_list"],
            "nb_notifications": donnees["nb_notifications"],
            "commandes_pretes_list": donnees["commandes_pretes_list"],
            "nb_messages": donnees["nb_messages"],
            "stock_rupture_count": 0,
            "stock_faible_count": 0,
        })
    else:
        context.update({
            "notifications_list": [],
            "nb_notifications": 0,
            "commandes_pretes_list": [],
            "nb_messages": 0,
            "stock_rupture_count": 0,
            "stock_faible_count": 0,
        })

    return context