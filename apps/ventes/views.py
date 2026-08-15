import json
from decimal import Decimal

from django.db import transaction
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.db.models import Q, Sum
from .models import DetailVente, Vente
from apps.menu.models import Produit
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser
from apps.parametres.models import ParametreRestaurant
from apps.commandes.models import Commande, LigneCommande


def _clamp_remise(remise):
    try:
        return max(0, min(100, float(remise or 0)))
    except (ValueError, TypeError):
        return 0.0


def _to_decimal(v):
    try:
        return Decimal(str(round(float(v), 2)))
    except (TypeError, ValueError):
        return None


def _charger_panier(panier, produits_ok=None):
    """Valide un panier [{id, qte}] et retourne {produit_id: (produit, quantite)}."""
    if not panier:
        raise ValueError("panier_vide")
    ids = [int(item.get("id")) for item in panier]
    produits = produits_ok or {p.id: p for p in Produit.objects.filter(id__in=ids)}
    lignes = []
    for item in panier:
        pid = int(item.get("id"))
        produit = produits.get(pid)
        if produit is None:
            raise ValueError("produit_introuvable")
        quantite = int(item.get("qte", 0))
        if quantite <= 0:
            raise ValueError(f"Quantité invalide : {produit.nom}")
        lignes.append((produit, quantite))
    return lignes



@role_required(["ADMIN", "GERANT", "CAISSIER"], ecriture_autorisee=True)
def pos(request):
    from apps.menu.models import Categorie
    from apps.tables.models import Table
    produits = Produit.objects.disponibles().select_related('categorie')
    categories = Categorie.objects.all()
    parametre = ParametreRestaurant.load()
    tables = Table.objects.all()

    commandes_ouvertes = list(
        Commande.objects.filter(payee=False)
        .select_related("table")
        .prefetch_related("lignes__produit")
    )

    commande_par_table = {}
    for commande in commandes_ouvertes:
        if commande.table_id and commande.table_id not in commande_par_table:
            commande_par_table[commande.table_id] = commande

    commandes_ouvertes_data = []
    for commande in commandes_ouvertes:
        commandes_ouvertes_data.append({
            "id": commande.id,
            "table_id": commande.table_id,
            "type": commande.type,
            "statut": commande.statut,
            "total": float(commande.total),
            "lignes": [
                {
                    "id": ligne.produit_id,
                    "nom": ligne.produit.nom,
                    "prix": float(ligne.prix),
                    "qte": ligne.quantite,
                }
                for ligne in commande.lignes.all()
            ],
        })

    today = timezone.now().date()
    ventes_jour = Vente.objects.filter(created_at__date=today, annulee=False)
    ca_jour = ventes_jour.aggregate(total=models.Sum("total"))["total"] or 0
    nb_ventes_jour = ventes_jour.count()
    nb_articles_jour = DetailVente.objects.filter(vente__in=ventes_jour).aggregate(
        total=models.Sum("quantite")
    )["total"] or 0

    return render(
        request,
        "ventes/pos.html",
        {
            "produits": produits,
            "categories": categories,
            "parametre": parametre,
            "tables": tables,
            "commandes_ouvertes": commandes_ouvertes,
            "commande_par_table": commande_par_table,
            "commandes_ouvertes_data": commandes_ouvertes_data,
            "statuts_commande": Commande.STATUTS,
            "types_commande": Vente.TYPE_COMMANDE,
            "ca_jour": ca_jour,
            "nb_ventes_jour": nb_ventes_jour,
            "nb_articles_jour": nb_articles_jour,
        }
    )


@role_required(["ADMIN", "GERANT", "CAISSIER"], ecriture_autorisee=True)
def creer_commande(request):
    """Crée (ou met à jour) une commande envoyée en cuisine."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Données invalides."}, status=400)

    panier = data.get("panier", [])
    table_id = data.get("table_id")
    type_cmd = data.get("type", Commande.SUR_PLACE)
    commande_id = data.get("commande_id")
    serveur = request.user if request.user.role == "SERVEUR" else None

    if type_cmd not in dict(Commande.TYPES):
        type_cmd = Commande.SUR_PLACE

    try:
        lignes = _charger_panier(panier)
    except ValueError as e:
        message = {
            "panier_vide": "Le panier est vide.",
            "produit_introuvable": "Produit introuvable.",
        }.get(str(e), str(e))
        if str(e) == "produit_introuvable":
            return JsonResponse({"success": False, "message": message}, status=404)
        return JsonResponse({"success": False, "message": message}, status=400)

    from apps.tables.models import Table
    table = None
    if table_id:
        table = Table.objects.filter(id=table_id).first()

    with transaction.atomic():
        commande = None
        nouveau = False
        if commande_id:
            commande = Commande.objects.filter(id=commande_id, payee=False).first()
        elif table and type_cmd in (Commande.SUR_PLACE,):
            commande = Commande.objects.filter(
                table=table, payee=False
            ).first()

        if commande is None:
            commande = Commande.objects.create(
                table=table,
                type=type_cmd,
                serveur=serveur,
                statut=Commande.EN_ATTENTE,
            )
            nouveau = True

        commande.lignes.all().delete()
        for produit, quantite in lignes:
            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=quantite,
                prix=produit.prix
            )

        if nouveau:
            from apps.notifications.utils import notifier_nouvelle_commande
            notifier_nouvelle_commande(commande)

    return JsonResponse({
        "success": True,
        "commande_id": commande.id,
        "commande_num": commande.id,
        "table": commande.table.numero if commande.table else None,
        "type": commande.get_type_display(),
        "statut": commande.get_statut_display(),
        "articles": commande.lignes.count(),
        "total": float(commande.total),
        "nouvelle": nouveau,
    })


@role_required(["ADMIN", "GERANT", "CAISSIER"], ecriture_autorisee=True)
def encaisser_commande(request):
    """Encaisse une commande : crée la vente, marque la commande payée."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Données invalides."}, status=400)

    commande_id = data.get("commande_id")
    commande = Commande.objects.filter(id=commande_id, payee=False).first()
    if commande is None:
        return JsonResponse({"success": False, "message": "Commande introuvable ou déjà payée."}, status=404)

    mode = data.get("mode_paiement")
    remise = _clamp_remise(data.get("remise", 0))

    lignes = list(commande.lignes.select_related("produit"))
    if not lignes:
        return JsonResponse({"success": False, "message": "La commande est vide."}, status=400)

    with transaction.atomic():
        vente = Vente.objects.create(
            caissier=request.user,
            table=commande.table,
            total=0,
            mode_paiement=mode,
            remise_pourcent=Decimal(str(remise)),
            type_commande=commande.type,
            montant_recu=_to_decimal(data.get("montant_recu") or None),
            monnaie_rendue=_to_decimal(data.get("monnaie_rendue") or None),
        )

        total_brut = Decimal("0")
        for ligne in lignes:
            sous_total = ligne.prix * ligne.quantite
            total_brut += sous_total
            DetailVente.objects.create(
                vente=vente,
                produit=ligne.produit,
                quantite=ligne.quantite,
                prix=ligne.prix,
                sous_total=sous_total
            )

        vente.total = total_brut * (1 - Decimal(str(remise)) / 100)
        vente.save()

        commande.vente = vente
        commande.payee = True
        commande.payee_le = timezone.now()
        commande.statut = Commande.LIVREE
        commande.save()

        from apps.commandes.models import Commande as C
        from apps.notifications.utils import notifier_changement_statut_commande
        notifier_changement_statut_commande(commande.id, C.EN_PREPARATION, C.LIVREE)

    return JsonResponse({
        "success": True,
        "vente_id": vente.id,
        "commande_id": commande.id,
        "total": float(vente.total),
    })


@role_required(["ADMIN", "GERANT", "CAISSIER"], ecriture_autorisee=True)
def enregistrer_vente(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Méthode non autorisée."
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Données invalides."
        }, status=400)

    panier = data.get("panier", [])
    mode = data.get("mode_paiement")
    table_id = data.get("table_id")
    remise = data.get("remise", 0)
    type_cmd = data.get("type_commande", "SUR_PLACE")
    montant_recu = data.get("montant_recu") or None
    monnaie_rendue = data.get("monnaie_rendue") or None
    nom_client_livraison = data.get("nom_client_livraison", "").strip()
    telephone_livraison = data.get("telephone_livraison", "").strip()
    adresse_livraison = data.get("adresse_livraison", "").strip()

    if type_cmd not in dict(Vente.TYPE_COMMANDE):
        type_cmd = "SUR_PLACE"

    if type_cmd == "LIVRAISON":
        if not adresse_livraison:
            return JsonResponse({
                "success": False,
                "message": "Adresse de livraison requise."
            }, status=400)
        if not telephone_livraison:
            return JsonResponse({
                "success": False,
                "message": "Téléphone de livraison requis."
            }, status=400)

    try:
        remise = max(0, min(100, float(remise or 0)))
    except (ValueError, TypeError):
        remise = 0

    if not panier:
        return JsonResponse({
            "success": False,
            "message": "Le panier est vide."
        }, status=400)

    ids_produits = [int(item.get("id")) for item in panier]
    produits = {
        produit.id: produit
        for produit in Produit.objects.disponibles().filter(id__in=ids_produits)
    }

    for item in panier:
        produit_id = int(item.get("id"))
        produit = produits.get(produit_id)

        if produit is None:
            return JsonResponse({
                "success": False,
                "message": "Produit introuvable."
            }, status=404)

        quantite = int(item.get("qte", 0))

        if quantite <= 0:
            return JsonResponse({
                "success": False,
                "message": f"Quantité invalide : {produit.nom}"
            }, status=400)

    total = 0

    table = None
    if table_id:
        from apps.tables.models import Table
        table = Table.objects.filter(id=table_id).first()

    with transaction.atomic():
        vente = Vente.objects.create(
            caissier=request.user,
            table=table,
            total=0,
            mode_paiement=mode,
            remise_pourcent=remise,
            type_commande=type_cmd,
            montant_recu=_to_decimal(montant_recu),
            monnaie_rendue=_to_decimal(monnaie_rendue),
        )

        for item in panier:
            produit = produits[int(item["id"])]
            quantite = int(item["qte"])
            prix = produit.prix
            sous_total = prix * quantite
            total += sous_total

            DetailVente.objects.create(
                vente=vente,
                produit=produit,
                quantite=quantite,
                prix=prix,
                sous_total=sous_total
            )

        vente.total = total * (1 - Decimal(str(remise)) / 100)
        vente.save()

        # Envoyer automatiquement la commande en cuisine (créée avec la vente)
        commande = Commande.objects.create(
            table=table,
            type=type_cmd,
            statut=Commande.EN_ATTENTE,
            vente=vente,
            payee=True,
            payee_le=timezone.now(),
            nom_client_livraison=nom_client_livraison,
            telephone_livraison=telephone_livraison,
            adresse_livraison=adresse_livraison,
        )
        for item in panier:
            produit = produits[int(item["id"])]
            quantite = int(item["qte"])
            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=quantite,
                prix=produit.prix,
            )

    from apps.notifications.utils import notifier_nouvelle_commande
    notifier_nouvelle_commande(commande)

    return JsonResponse({
        "success": True,
        "vente_id": vente.id,
        "commande_id": commande.id,
    })


@role_required(["ADMIN", "GERANT", "CAISSIER"])
def ticket(request, vente_id):
    vente = get_object_or_404(
        Vente.objects.prefetch_related("details__produit"),
        id=vente_id
    )
    parametre = ParametreRestaurant.load()

    return render(
        request,
        "ventes/ticket.html",
        {
            "vente": vente,
            "parametre": parametre,
        }
    )


@role_required(["ADMIN", "GERANT", "CAISSIER"])
def detail_vente(request, vente_id):
    vente = get_object_or_404(
        Vente.objects.select_related("caissier", "annule_par", "commande")
        .prefetch_related("details__produit"),
        id=vente_id
    )
    parametre = ParametreRestaurant.load()

    return render(
        request,
        "ventes/detail.html",
        {
            "vente": vente,
            "parametre": parametre,
        }
    )


@role_required(["CAISSIER"])
def annuler_vente(request, vente_id):
    """Annule une vente."""
    vente = get_object_or_404(Vente, id=vente_id)

    if vente.annulee:
        messages.error(request, "Cette vente a déjà été annulée.")
        return redirect("ventes:detail", vente_id=vente.id)

    if request.method == "POST":
        with transaction.atomic():
            vente.annulee = True
            vente.annule_le = timezone.now()
            vente.annule_par = request.user
            vente.save()

        messages.success(
            request,
            f"Vente N° {vente.id} annulée."
        )
        return redirect("ventes:historique")

    return render(request, "ventes/annuler.html", {"vente": vente})


@role_required(["ADMIN", "GERANT", "CAISSIER"])
def historique(request):

    ventes = Vente.objects.select_related("caissier").order_by("-created_at")

    # Filtres serveur
    q = request.GET.get("q", "").strip()
    date = request.GET.get("date", "").strip()
    statut = request.GET.get("statut", "").strip()
    paiement = request.GET.get("paiement", "").strip()
    date_debut = request.GET.get("date_debut", "").strip()
    date_fin = request.GET.get("date_fin", "").strip()

    if q:
        ventes = ventes.filter(
            Q(id__icontains=q) | Q(caissier__username__icontains=q)
        )
    if date:
        ventes = ventes.filter(created_at__date=date)
    if statut == "annulees":
        ventes = ventes.filter(annulee=True)
    elif statut == "valides":
        ventes = ventes.filter(annulee=False)
    if paiement:
        ventes = ventes.filter(mode_paiement=paiement)
    if date_debut:
        ventes = ventes.filter(created_at__date__gte=date_debut)
    if date_fin:
        ventes = ventes.filter(created_at__date__lte=date_fin)

    sessions = Session.objects.filter(
        expire_date__gte=timezone.now()
    )

    users_online = []

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get("_auth_user_id")
        if user_id:
            users_online.append(user_id)

    users_online = list(set(users_online))

    utilisateurs_connectes = CustomUser.objects.filter(
        id__in=users_online,
        is_active=True
    )

    total = ventes.aggregate(total=Sum("total"))["total"] or 0
    total_valides = (
        ventes.filter(annulee=False).aggregate(total=Sum("total"))["total"] or 0
    )
    total_annulees = (
        ventes.filter(annulee=True).aggregate(total=Sum("total"))["total"] or 0
    )

    paginator = Paginator(ventes, 20)
    page_num = request.GET.get("page", "1")
    try:
        page_obj = paginator.page(page_num)
    except Exception:
        page_obj = paginator.page(1)

    return render(
        request,
        "ventes/historique.html",
        {
            "ventes": page_obj.object_list,
            "page_obj": page_obj,
            "total": total,
            "total_annulees": total_annulees,
            "total_valides": total_valides,
            "utilisateurs_connectes": utilisateurs_connectes,
            "nombre_connectes": utilisateurs_connectes.count(),
            "modes_paiement": dict(Vente.MODE_PAIEMENT),
            "q": q,
            "date": date,
            "statut": statut,
            "paiement": paiement,
            "date_debut": date_debut,
            "date_fin": date_fin,
        }
    )