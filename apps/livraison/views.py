import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.livraison.models import Livraison
from apps.commandes.models import Commande
from apps.accounts.models import CustomUser
from apps.accounts.decorators import role_required
from apps.notifications.utils import envoyer_notification_broadcast


@role_required(["ADMIN", "LIVREUR"])
def index(request):
    """Liste des livraisons."""
    livraisons = Livraison.objects.select_related(
        "commande", "livreur"
    ).prefetch_related(
        "commande__lignes__produit"
    ).all()

    # Commandes prêtes sans livraison encore créée
    commandes_pretes = Commande.objects.filter(
        statut=Commande.PRETE
    ).exclude(
        livraisons__statut__in=[
            Livraison.EN_ATTENTE,
            Livraison.EN_COURS,
            Livraison.LIVREE
        ]
    ).prefetch_related("lignes__produit")

    stats = {
        "en_attente": livraisons.filter(statut=Livraison.EN_ATTENTE).count(),
        "en_cours": livraisons.filter(statut=Livraison.EN_COURS).count(),
        "livrees": livraisons.filter(statut=Livraison.LIVREE).count(),
        "annulees": livraisons.filter(statut=Livraison.ANNULEE).count(),
    }

    return render(request, "livraison/index.html", {
        "livraisons": livraisons,
        "commandes_pretes": commandes_pretes,
        "stats": stats,
        "groupe": "livraison",
    })


@role_required(["LIVREUR"])
def creer_livraison(request, commande_id):
    """Crée une livraison pour une commande prête."""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    commande = get_object_or_404(Commande, pk=commande_id, statut=Commande.PRETE)

    # Vérifier qu'il n'y a pas déjà une livraison active
    livraison_existante = Livraison.objects.filter(
        commande=commande,
        statut__in=[Livraison.EN_ATTENTE, Livraison.EN_COURS]
    ).exists()

    if livraison_existante:
        return JsonResponse({
            "error": "Un livraison existe déjà pour cette commande."
        }, status=400)

    livraison = Livraison.objects.create(
        commande=commande,
        adresse=commande.adresse_livraison or "",
        telephone=commande.telephone_livraison or "",
        statut=Livraison.EN_ATTENTE,
    )

    envoyer_notification_broadcast(
        "livraison",
        "nouvelle_livraison",
        {
            "id": livraison.id,
            "commande_id": commande.id,
            "adresse": livraison.adresse,
            "telephone": livraison.telephone,
        }
    )

    return JsonResponse({"success": True, "livraison_id": livraison.id})


@role_required(["LIVREUR"])
@require_POST
def maj_position(request, pk):
    """Met à jour la position GPS d'une livraison depuis l'appareil du livreur."""
    livraison = get_object_or_404(Livraison, pk=pk)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Données invalides"}, status=400)

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if latitude is None or longitude is None:
        return JsonResponse({"success": False, "message": "Latitude/longitude requises"}, status=400)

    livraison.latitude = float(latitude)
    livraison.longitude = float(longitude)
    if livraison.statut == Livraison.EN_ATTENTE:
        livraison.statut = Livraison.EN_COURS
    if not livraison.livreur:
        livraison.livreur = request.user
    livraison.save(update_fields=["latitude", "longitude", "statut", "livreur", "updated_at"])

    envoyer_notification_broadcast(
        "livraison",
        "position_livraison",
        {
            "livraison_id": livraison.id,
            "commande_id": livraison.commande_id,
            "latitude": livraison.latitude,
            "longitude": livraison.longitude,
            "statut": livraison.statut,
        },
    )

    return JsonResponse({"success": True, "latitude": livraison.latitude, "longitude": livraison.longitude})


def suivi_commande(request, commande_id, token):
    """Page publique de suivi pour le client (protégée par token secret)."""
    commande = get_object_or_404(Commande, pk=commande_id)
    if commande.token != token:
        raise Http404("Lien de suivi invalide.")
    livraison = commande.livraisons.order_by("-created_at").first()
    if not livraison:
        return render(request, "livraison/suivi.html", {
            "commande": commande,
            "livraison": None,
            "groupe": "livraison",
        })

    return render(request, "livraison/suivi.html", {
        "commande": commande,
        "livraison": livraison,
        "groupe": "livraison",
    })


@role_required(["ADMIN", "LIVREUR"])
def detail(request, pk):
    """Détail complet d'une livraison."""
    livraison = get_object_or_404(
        Livraison.objects.select_related("commande", "livreur"),
        pk=pk
    )
    livreurs = CustomUser.objects.filter(role="LIVREUR", is_active=True)

    return render(request, "livraison/detail.html", {
        "livraison": livraison,
        "livreurs": livreurs,
        "groupe": "livraison",
    })


@role_required(["LIVREUR"])
def modifier(request, pk):
    """Modifier une livraison (adresse, téléphone, notes, livreur)."""
    livraison = get_object_or_404(Livraison, pk=pk)

    if request.method == "POST":
        livraison.adresse = request.POST.get("adresse", "").strip()
        livraison.telephone = request.POST.get("telephone", "").strip()
        livraison.notes = request.POST.get("notes", "").strip()

        livreur_id = request.POST.get("livreur")
        if livreur_id:
            livreur = get_object_or_404(
                CustomUser, pk=livreur_id, role="LIVREUR", is_active=True
            )
            livraison.livreur = livreur
        else:
            livraison.livreur = None

        livraison.save()
        messages.success(request, "Livraison mise à jour.")
        return redirect("livraison:detail", pk=livraison.pk)

    livreurs = CustomUser.objects.filter(role="LIVREUR", is_active=True)
    return render(request, "livraison/form.html", {
        "livraison": livraison,
        "livreurs": livreurs,
    })


@role_required(["LIVREUR"])
def supprimer(request, pk):
    """Supprimer une livraison."""
    livraison = get_object_or_404(Livraison, pk=pk)

    if request.method == "POST":
        livraison.delete()
        messages.success(request, "Livraison supprimée.")
        return redirect("livraison:liste")

    return render(request, "livraison/supprimer.html", {"livraison": livraison})


@role_required(["LIVREUR"])
def changer_statut(request, pk):
    """Change le statut d'une livraison (AJAX)."""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    livraison = get_object_or_404(Livraison, pk=pk)
    nouveau_statut = request.POST.get("statut")

    statuts_valides = [s[0] for s in Livraison.STATUTS]
    if nouveau_statut not in statuts_valides:
        return JsonResponse({"error": "Statut invalide"}, status=400)

    ancien_statut = livraison.statut
    livraison.statut = nouveau_statut

    # Si livrée, on enregistre la date et on met à jour la commande
    if nouveau_statut == Livraison.LIVREE:
        livraison.date_livraison = timezone.now()
        livraison.livreur = request.user
        # Mettre à jour le statut de la commande associée
        commande = livraison.commande
        if commande.statut != Commande.LIVREE:
            commande.statut = Commande.LIVREE
            commande.save()

    elif nouveau_statut == Livraison.EN_COURS and not livraison.livreur:
        livraison.livreur = request.user

    livraison.save()

    envoyer_notification_broadcast(
        "livraison",
        "statut_livraison",
        {
            "id": livraison.id,
            "commande_id": livraison.commande_id,
            "ancien_statut": dict(Livraison.STATUTS).get(ancien_statut, ancien_statut),
            "nouveau_statut": dict(Livraison.STATUTS).get(nouveau_statut, nouveau_statut),
        }
    )

    return JsonResponse({
        "success": True,
        "id": livraison.id,
        "ancien_statut": ancien_statut,
        "nouveau_statut": nouveau_statut,
        "statut_display": livraison.get_statut_display(),
    })


def api_position(request, commande_id, token):
    """API publique JSON — retourne la position du livreur pour une commande.
    Utilisée par le client pour le polling temps réel (sans WebSocket).
    Protégée par le token secret de la commande.
    """
    commande = get_object_or_404(Commande, pk=commande_id)
    if commande.token != token:
        raise Http404("Lien de suivi invalide.")
    livraison = commande.livraisons.order_by("-created_at").first()

    if not livraison:
        return JsonResponse({
            "found": False,
            "statut": "EN_ATTENTE",
            "statut_display": "En attente",
            "latitude": None,
            "longitude": None,
        })

    return JsonResponse({
        "found": True,
        "livraison_id": livraison.id,
        "statut": livraison.statut,
        "statut_display": livraison.get_statut_display(),
        "latitude": livraison.latitude,
        "longitude": livraison.longitude,
        "latitude_client": commande.latitude_client,
        "longitude_client": commande.longitude_client,
        "adresse": livraison.adresse,
        "nom_client": commande.nom_client_livraison,
        "telephone": livraison.telephone,
    })
