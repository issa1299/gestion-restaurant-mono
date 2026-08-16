import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.db.models import Prefetch
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.accounts.decorators import role_required
from apps.notifications.utils import envoyer_notification_broadcast
from apps.parametres.models import ParametreRestaurant
from .email_utils import envoyer_reponse_message, envoyer_confirmation_reservation
from .models import Reservation, ContactMessage, PhotoGalerie, Temoignage


def bienvenue(request):
    """Page de bienvenue (splash) affichée avant d'entrer sur le site."""
    return render(request, "site/bienvenue.html")


def accueil(request):
    """Page d'accueil publique du restaurant"""
    return render(request, "site/accueil.html")


def a_propos(request):
    """Page de présentation du restaurant"""
    return render(request, "site/a_propos.html")


def galerie(request):
    """Galerie de photos"""
    photos = PhotoGalerie.objects.all()
    return render(request, "site/galerie.html", {"photos": photos})


def livraison(request):
    """Informations sur la livraison"""
    return render(request, "site/livraison.html")


def temoignages(request):
    """Avis des clients"""
    temoignages = Temoignage.objects.filter(actif=True)
    return render(request, "site/temoignages.html", {"temoignages": temoignages})


def contact(request):
    """Page contact avec formulaire"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        email = request.POST.get("email", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        sujet = request.POST.get("sujet", "").strip()
        message = request.POST.get("message", "").strip()

        if not nom or not email or not message:
            messages.error(request, "Nom, email et message sont requis.")
            return redirect("restaurant:contact")

        ContactMessage.objects.create(
            nom=nom,
            email=email,
            telephone=telephone,
            sujet=sujet,
            message=message,
        )
        messages.success(request, "Votre message a bien été envoyé. Merci !")
        envoyer_notification_broadcast("dashboard", "nouveau_message", {
            "nom": nom,
            "email": email,
            "sujet": sujet or "Message de contact",
        })
        return redirect("restaurant:contact")

    return render(request, "site/contact.html")


def reserver(request):
    """Page de réservation de table"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        email = request.POST.get("email", "").strip()
        date = request.POST.get("date", "")
        heure = request.POST.get("heure", "")
        personnes = request.POST.get("nombre_personnes", "2")
        message = request.POST.get("message", "").strip()

        if not nom or not telephone or not date or not heure:
            messages.error(request, "Nom, téléphone, date et heure sont requis.")
            return redirect("restaurant:reserver")

        try:
            personnes = int(personnes)
            if personnes < 1:
                raise ValueError
        except (ValueError, TypeError):
            personnes = 2

        Reservation.objects.create(
            nom=nom,
            telephone=telephone,
            email=email,
            date=date,
            heure=heure,
            nombre_personnes=personnes,
            message=message,
        )
        messages.success(
            request,
            f"Votre réservation du {date} à {heure} a bien été enregistrée. "
            f"Nous vous attendons !",
        )
        envoyer_notification_broadcast("dashboard", "nouvelle_reservation", {
            "nom": nom,
            "telephone": telephone,
            "date": date,
            "heure": str(heure),
            "personnes": personnes,
        })
        return redirect("restaurant:reserver")

    return render(request, "site/reserver.html")


@role_required(["ADMIN", "GERANT", "SERVEUR", "CAISSIER"], ecriture_autorisee=True)
def changer_statut_reservation(request, pk):
    """Confirmer ou annuler une réservation depuis le dashboard"""
    reservation = get_object_or_404(Reservation, pk=pk)
    statut = request.POST.get("statut")
    source = request.POST.get("source", "dashboard")

    if statut in (Reservation.CONFIRMEE, Reservation.ANNULEE):
        ancien = reservation.statut
        reservation.statut = statut
        reservation.save()
        libelles = dict(Reservation.STATUTS)
        messages.success(
            request,
            f"Réservation de {reservation.nom} : "
            f"{libelles.get(ancien, ancien)} → {libelles.get(statut)}.",
        )
        envoyer_notification_broadcast("dashboard", "statut_reservation", {
            "id": reservation.id,
            "nom": reservation.nom,
            "statut": libelles.get(statut),
        })
        ok, erreur = envoyer_confirmation_reservation(reservation)
        if ok:
            messages.success(request, f"Email de confirmation envoyé à {reservation.nom}.")
        elif erreur:
            messages.warning(request, f"Email non envoyé : {erreur}")
    else:
        messages.error(request, "Statut invalide.")

    if source == "reservations":
        return redirect("restaurant:reservations")
    return redirect("dashboard:index")


@role_required(["ADMIN", "GERANT", "SERVEUR", "CAISSIER"])
def marquer_message_lu(request, pk):
    """Marquer un message de contact comme lu (ou non lu)"""
    message = get_object_or_404(ContactMessage, pk=pk)
    lu = request.POST.get("lu", "1") == "1"
    message.lu = lu
    message.save()
    if lu:
        messages.success(request, f"Message de {message.nom} marqué comme lu.")
    else:
        messages.success(request, f"Message de {message.nom} marqué comme non lu.")
    if request.POST.get("source") == "messages":
        return redirect("restaurant:messages")
    return redirect("dashboard:index")


@role_required(["ADMIN", "GERANT", "SERVEUR", "CAISSIER"], ecriture_autorisee=True)
def repondre_message(request, pk):
    """Répondre par email à un message de contact"""
    message_contact = get_object_or_404(ContactMessage, pk=pk)
    reponse = request.POST.get("reponse", "").strip()
    if not reponse:
        messages.error(request, "La réponse ne peut pas être vide.")
        return redirect("restaurant:messages")

    ok, erreur = envoyer_reponse_message(message_contact, reponse)
    message_contact.reponse = reponse
    message_contact.lu = True
    message_contact.save()
    if ok:
        message_contact.repondu_le = timezone.now()
        message_contact.save()
        messages.success(request, f"Réponse envoyée à {message_contact.nom}.")
    else:
        messages.error(request, f"Échec de l'envoi : {erreur}. La réponse est enregistrée en brouillon.")

    if request.POST.get("source") == "messages":
        return redirect("restaurant:messages")
    return redirect("dashboard:index")


@role_required(["ADMIN", "GERANT", "SERVEUR", "CAISSIER"])
def liste_reservations(request):
    """Historique complet des réservations avec filtre par statut"""
    statut = request.GET.get("statut", "")
    reservations = Reservation.objects.all()
    if statut in dict(Reservation.STATUTS):
        reservations = reservations.filter(statut=statut)
    return render(request, "restaurant/reservations.html", {
        "reservations": reservations,
        "statuts": Reservation.STATUTS,
        "statut_selectionne": statut,
        "groupe": "dashboard",
    })


@role_required(["ADMIN", "GERANT", "SERVEUR", "CAISSIER"])
def liste_messages(request):
    """Liste des messages de contact avec filtre lu / non lu"""
    filtre = request.GET.get("filtre", "")
    messages_list = ContactMessage.objects.all()
    if filtre == "lus":
        messages_list = messages_list.filter(lu=True)
    elif filtre == "non_lus":
        messages_list = messages_list.filter(lu=False)
    return render(request, "restaurant/messages.html", {
        "messages_list": messages_list,
        "filtre": filtre,
        "groupe": "dashboard",
    })


@role_required(["ADMIN", "GERANT"])
def galerie_gestion(request):
    """Gestion interne des photos de la galerie"""
    if request.method == "POST":
        image = request.FILES.get("image")
        if not image:
            messages.error(request, "Veuillez sélectionner une image.")
        else:
            PhotoGalerie.objects.create(
                titre=request.POST.get("titre", "").strip(),
                image=image,
                description=request.POST.get("description", "").strip(),
            )
            messages.success(request, "Photo ajoutée à la galerie.")
        return redirect("restaurant:galerie_gestion")

    photos = PhotoGalerie.objects.all()
    return render(request, "restaurant/galerie_gestion.html", {
        "photos": photos,
        "photos_avec_titre": photos.exclude(titre="").count(),
        "groupe": "dashboard",
    })


@role_required(["ADMIN", "GERANT"])
def galerie_supprimer(request, pk):
    """Supprimer une photo de la galerie"""
    if request.method != "POST":
        return redirect("restaurant:galerie_gestion")
    photo = get_object_or_404(PhotoGalerie, pk=pk)
    titre = photo.titre or f"Photo {photo.id}"
    photo.delete()
    messages.success(request, f"Photo « {titre} » supprimée.")
    return redirect("restaurant:galerie_gestion")


@role_required(["ADMIN", "GERANT"])
def temoignages_gestion(request):
    """Liste et gestion des témoignages (admin)"""
    temoignages_list = Temoignage.objects.all()
    actifs = Temoignage.objects.filter(actif=True).count()
    inactifs = Temoignage.objects.filter(actif=False).count()

    return render(request, "restaurant/temoignages_gestion.html", {
        "temoignages_list": temoignages_list,
        "actifs": actifs,
        "inactifs": inactifs,
        "total": temoignages_list.count(),
        "groupe": "dashboard",
    })


@role_required(["ADMIN", "GERANT"])
def temoignage_ajouter(request):
    """Créer un témoignage"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        note = request.POST.get("note", "5")
        message = request.POST.get("message", "").strip()
        actif = request.POST.get("actif") == "on"

        if not nom or not message:
            messages.error(request, "Le nom et le message sont requis.")
            return redirect("restaurant:temoignage_ajouter")

        try:
            note = int(note)
            if note < 1 or note > 5:
                raise ValueError
        except (ValueError, TypeError):
            note = 5

        Temoignage.objects.create(
            nom=nom,
            note=note,
            message=message,
            actif=actif,
        )
        messages.success(request, "Témoignage ajouté avec succès.")
        return redirect("restaurant:temoignages_gestion")

    return render(request, "restaurant/temoignage_form.html", {"edition": False})


@role_required(["ADMIN", "GERANT"])
def temoignage_modifier(request, pk):
    """Modifier un témoignage"""
    temoignage = get_object_or_404(Temoignage, pk=pk)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        note = request.POST.get("note", "5")
        message = request.POST.get("message", "").strip()
        actif = request.POST.get("actif") == "on"

        if not nom or not message:
            messages.error(request, "Le nom et le message sont requis.")
            return redirect("restaurant:temoignage_modifier", pk=pk)

        try:
            note = int(note)
            if note < 1 or note > 5:
                raise ValueError
        except (ValueError, TypeError):
            note = 5

        temoignage.nom = nom
        temoignage.note = note
        temoignage.message = message
        temoignage.actif = actif
        temoignage.save()

        messages.success(request, "Témoignage modifié avec succès.")
        return redirect("restaurant:temoignages_gestion")

    return render(request, "restaurant/temoignage_form.html", {
        "temoignage": temoignage,
        "edition": True,
    })


@role_required(["ADMIN", "GERANT"])
def temoignage_supprimer(request, pk):
    """Supprimer un témoignage"""
    temoignage = get_object_or_404(Temoignage, pk=pk)

    if request.method == "POST":
        nom = temoignage.nom
        temoignage.delete()
        messages.success(request, f"Témoignage de « {nom} » supprimé.")
        return redirect("restaurant:temoignages_gestion")

    return render(request, "restaurant/temoignage_supprimer.html", {
        "temoignage": temoignage,
    })


@role_required(["ADMIN", "GERANT"])
def temoignage_toggle(request, pk):
    """Activer / désactiver un témoignage"""
    if request.method != "POST":
        return redirect("restaurant:temoignages_gestion")
    temoignage = get_object_or_404(Temoignage, pk=pk)
    temoignage.actif = not temoignage.actif
    temoignage.save()
    statut = "activé" if temoignage.actif else "désactivé"
    messages.success(request, f"Témoignage de « {temoignage.nom} » {statut}.")
    return redirect("restaurant:temoignages_gestion")


@ensure_csrf_cookie
def commander_en_ligne(request):
    """Page publique de commande en ligne avec géolocalisation du client."""
    from apps.menu.models import Categorie, Produit
    from apps.commandes.models import Commande, LigneCommande
    import json

    categories = Categorie.objects.prefetch_related(
        Prefetch("produits", queryset=Produit.objects.disponibles())
    ).filter(produits__disponible=True).distinct()

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        adresse = request.POST.get("adresse", "").strip()
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()
        produits_json = request.POST.get("produits_json", "[]")

        if not nom or not telephone or not adresse:
            messages.error(request, "Nom, téléphone et adresse sont requis.")
            return redirect("restaurant:commander")

        try:
            produits_data = json.loads(produits_json)
        except (json.JSONDecodeError, ValueError):
            produits_data = []

        if not produits_data:
            messages.error(request, "Veuillez sélectionner au moins un article.")
            return redirect("restaurant:commander")

        # Coordonnées GPS : ignorées si invalides
        try:
            latitude_client = float(latitude) if latitude else None
        except (ValueError, TypeError):
            latitude_client = None
        try:
            longitude_client = float(longitude) if longitude else None
        except (ValueError, TypeError):
            longitude_client = None

        # Créer la commande
        commande = Commande.objects.create(
            type=Commande.LIVRAISON,
            statut=Commande.EN_ATTENTE,
            adresse_livraison=adresse,
            telephone_livraison=telephone,
            nom_client_livraison=nom,
            latitude_client=latitude_client,
            longitude_client=longitude_client,
        )

        # Ajouter les lignes
        for item in produits_data:
            try:
                produit = Produit.objects.disponibles().filter(pk=item["id"]).first()
                if produit is None:
                    continue
                quantite = max(1, int(item.get("quantite", 1)))
                LigneCommande.objects.create(
                    commande=commande,
                    produit=produit,
                    quantite=quantite,
                    prix=produit.prix,
                )
            except (Produit.DoesNotExist, KeyError, ValueError):
                continue

        # Vérifier qu'on a bien des lignes
        if not commande.lignes.exists():
            commande.delete()
            messages.error(request, "Produits invalides. Veuillez réessayer.")
            return redirect("restaurant:commander")

        # Notifier le staff
        envoyer_notification_broadcast("commandes", "nouvelle_commande", {
            "id": commande.id,
            "table": "Livraison",
            "nom_client": nom,
            "adresse": adresse,
            "articles": [
                {"nom": l.produit.nom, "quantite": l.quantite}
                for l in commande.lignes.select_related("produit")
            ],
        })
        envoyer_notification_broadcast("dashboard", "nouvelle_commande", {
            "id": commande.id,
            "nom_client": nom,
        })

        return redirect("restaurant:confirmation_commande", commande_id=commande.id, token=commande.token)

    return render(request, "site/commander.html", {
        "categories": categories,
    })


def confirmation_commande(request, commande_id, token):
    """Page de confirmation après commande en ligne — affiche le lien de suivi.
    Protégée par le token secret de la commande.
    """
    from apps.commandes.models import Commande
    commande = get_object_or_404(Commande, pk=commande_id)
    if commande.token != token:
        raise Http404("Lien de confirmation invalide.")
    lien_suivi = request.build_absolute_uri(f"/livraisons/suivi/{commande.id}/{commande.token}/")
    return render(request, "site/confirmation_commande.html", {
        "commande": commande,
        "lien_suivi": lien_suivi,
    })


def manifest(request):
    """Web App Manifest pour le PWA."""
    parametre = ParametreRestaurant.load()
    icone = request.build_absolute_uri(reverse("pwa_icon", kwargs={"taille": 512}))
    icone_192 = request.build_absolute_uri(reverse("pwa_icon", kwargs={"taille": 192}))
    data = {
        "name": parametre.nom or "RestaurantPro",
        "short_name": parametre.nom[:12] or "Restaurant",
        "description": "Commandez en ligne et suivez vos livraisons.",
        "id": "/",
        "start_url": "/accueil/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f97316",
        "theme_color": "#f97316",
        "orientation": "portrait",
        "icons": [
            {"src": icone_192, "sizes": "192x192", "type": "image/png"},
            {"src": icone, "sizes": "512x512", "type": "image/png"},
            {"src": icone, "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return JsonResponse(data)


def pwa_icon(request, taille):
    """Icône PWA générée depuis le logo du restaurant (repli : icône statique)."""
    from PIL import Image
    from django.conf import settings
    from io import BytesIO

    taille = int(taille)
    parametre = ParametreRestaurant.load()

    chemin = None
    if parametre.logo:
        p = parametre.logo.path
        if os.path.exists(p):
            chemin = p
    if chemin is None:
        chemin = os.path.join(settings.STATIC_ROOT if not settings.DEBUG else settings.BASE_DIR, "static", "img", "icon-512.png")
        if not os.path.exists(chemin):
            chemin = os.path.join(settings.BASE_DIR, "static", "img", "icon-512.png")

    img = Image.open(chemin)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    if img.size != (taille, taille):
        img = img.resize((taille, taille), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="PNG")
    response = HttpResponse(buf.getvalue(), content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    return response


def service_worker(request):
    """Service worker servé à la racine pour couvrir tout le site."""
    return HttpResponse(SERVICE_WORKER_JS, content_type="application/javascript")


SERVICE_WORKER_JS = r"""
const CACHE_VERS = 'restaurantpro-v1';
const APP_SHELL = [
  '/accueil/',
  '/static/js/toast.js',
  '/static/img/icon-192.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERS).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_VERS).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Navigation : réseau d'abord, repli sur le cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  // Les pages HTML : réseau d'abord, sinon cache
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_VERS).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match('/accueil/')))
    );
    return;
  }

  // Statiques et images : cache d'abord, sinon réseau puis mise en cache
  if (request.destination === 'style' || request.destination === 'script' || request.destination === 'image' || request.destination === 'font') {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          const copy = response.clone();
          caches.open(CACHE_VERS).then((cache) => cache.put(request, copy));
          return response;
        });
      })
    );
  }
});
"""
