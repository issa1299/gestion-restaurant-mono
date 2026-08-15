from django.shortcuts import render
from apps.commandes.models import Commande, LigneCommande
from apps.accounts.decorators import role_required
from apps.ventes.models import Vente
from apps.clients.models import Client
from apps.tables.models import Table
from apps.restaurant.models import Reservation, ContactMessage
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate


def _periode(periode):
    """Retourne (debut, fin, label) pour une période donnée."""
    aujourd_hui = timezone.localdate()
    if periode == "aujourdhui":
        return aujourd_hui, aujourd_hui, "Aujourd'hui"
    if periode == "hier":
        hier = aujourd_hui - timedelta(days=1)
        return hier, hier, "Hier"
    if periode == "30j":
        return aujourd_hui - timedelta(days=29), aujourd_hui, "30 derniers jours"
    return aujourd_hui - timedelta(days=6), aujourd_hui, "7 derniers jours"


PERIODES = [
    ("aujourdhui", "Aujourd'hui"),
    ("hier", "Hier"),
    ("7j", "7 jours"),
    ("30j", "30 jours"),
]


@role_required(["ADMIN", "GERANT", "SERVEUR", "CUISINIER", "CAISSIER"])
def index(request):
    """Vue du dashboard avec données réelles."""

    periode = request.GET.get("periode", "7j")
    if periode not in [p[0] for p in PERIODES]:
        periode = "7j"

    debut, fin, label_periode = _periode(periode)

    # Gérant : accès complet. Les autres rôles voient la vue simple.
    est_gerant = request.user.role in ("ADMIN", "GERANT") or request.user.is_superuser

    # Commandes non annulées de la période (pour répartition/top produits)
    commandes_periode = Commande.objects.filter(
        created_at__date__gte=debut,
        created_at__date__lte=fin,
    ).exclude(statut=Commande.ANNULEE)

    lignes_periode = LigneCommande.objects.filter(
        commande__created_at__date__gte=debut,
        commande__created_at__date__lte=fin,
    ).exclude(commande__statut=Commande.ANNULEE)

    # Chiffre d'affaires (ventes encaissées, non annulées)
    ca_total = float(
        Vente.objects.filter(
            created_at__date__gte=debut,
            created_at__date__lte=fin,
            annulee=False,
        ).aggregate(total=Sum("total"))["total"] or 0
    )

    # Nombre de commandes (non annulées)
    nb_commandes = commandes_periode.count()

    # Ticket moyen
    ticket_moyen = ca_total / nb_commandes if nb_commandes else 0

    # CA par type (Sur place / À emporter / Livraison)
    ca_par_type = {}
    type_rows = lignes_periode.values("commande__type").annotate(
        ca_type=Sum(F("quantite") * F("prix"))
    )
    for row in type_rows:
        type_code = row["commande__type"]
        if type_code:
            ca_par_type[type_code] = float(row["ca_type"] or 0)
    for code, _ in Commande.TYPES:
        ca_par_type.setdefault(code, 0.0)
    ca_types_total = sum(ca_par_type.values())

    # Top produits vendus
    top_produits = (
        lignes_periode.values("produit__nom")
        .annotate(
            quantite_totale=Sum("quantite"),
            ca_produit=Sum(F("quantite") * F("prix")),
        )
        .order_by("-ca_produit")[:5]
    )

    # Commandes aujourd'hui
    commandes_ajourdhui = Commande.objects.filter(
        created_at__date=timezone.localdate()
    ).count()

    # Total clients
    total_clients = Client.objects.count()

    # Tables occupées
    tables_occupees = Table.objects.filter(disponible=False).count()

    # Dernières commandes
    dernieres_commandes = Commande.objects.select_related(
        "client", "table"
    ).prefetch_related("lignes")[:5]

    # Ventes des 7 derniers jours (graphique)
    il_y_a_7_jours = timezone.localdate() - timedelta(days=6)
    ventes_7jours = Vente.objects.filter(
        created_at__date__gte=il_y_a_7_jours,
        annulee=False,
    )
    ventes_par_jour = (
        ventes_7jours.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(ca_jour=Sum("total"), nb=Count("id"))
        .order_by("date")
    )
    dates_chart = [v["date"].strftime("%d/%m") for v in ventes_par_jour]
    ca_chart = [float(v["ca_jour"]) for v in ventes_par_jour]

    # Réservations à confirmer et messages non lus
    reservations_recentes = Reservation.objects.filter(
        statut=Reservation.EN_ATTENTE
    )[:5]
    reservations_count = Reservation.objects.filter(
        statut=Reservation.EN_ATTENTE
    ).count()
    messages_non_lus = ContactMessage.objects.filter(lu=False)[:5]
    messages_non_lus_count = ContactMessage.objects.filter(lu=False).count()

    return render(
        request,
        "dashboard/index.html",
        {
            "groupe": "dashboard",
            "periode": periode,
            "periodes": PERIODES,
            "label_periode": label_periode,
            "est_gerant": est_gerant,
            "ca_total": ca_total,
            "nb_commandes": nb_commandes,
            "ticket_moyen": ticket_moyen,
            "ca_par_type": ca_par_type,
            "ca_types_total": ca_types_total,
            "top_produits": top_produits,
            "commandes_ajourdhui": commandes_ajourdhui,
            "total_clients": total_clients,
            "tables_occupees": tables_occupees,
            "dernieres_commandes": dernieres_commandes,
            "dates_chart": dates_chart,
            "ca_chart": ca_chart,
            "reservations_recentes": reservations_recentes,
            "reservations_count": reservations_count,
            "messages_non_lus": messages_non_lus,
            "messages_non_lus_count": messages_non_lus_count,
        }
    )