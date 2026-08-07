# TODO — Suivi de Livraison en Temps Réel

## Backend — Commandes en ligne (GPS client)

- [x] C. Corriger `apps/commandes/views.py` → `client_passer_commande`
      - Stockage de `latitude_client` / `longitude_client` dans la commande
      - Stockage de `nom_client_livraison` (nom du client guest/connecté)
      - Normalisation robuste des coordonnées GPS (gestion None/vide)

## Étapes restantes (templates uniquement — backend déjà implémenté)

- [x] 1. Créer `templates/site/confirmation_commande.html`
      - Confirmation visuelle commande N° + total
      - Lien de suivi cliquable/copiable
      - QR code optionnel
      - Base `base_site.html`

- [x] 2. Refondre `templates/livraison/suivi.html`
      - Carte Leaflet plein écran, 2 marqueurs (🏠 client + 🛵 livreur)
      - Timeline de statut (En attente → En préparation → Prête → En livraison → Livrée)
      - Polling AJAX toutes les 5s sur `api_position`
      - Ligne de trajet dynamique
      - Design premium style app mobile

- [x] 3. Améliorer `templates/livraison/detail.html`
      - 2 marqueurs : 🏠 client (fixe) + 🛵 livreur (mobile)
      - Bouton "Démarrer le partage GPS" → géolocalisation continue (watchPosition, envoi 5s)
      - Ligne de trajet sur la carte
      - Boutons de changement de statut

- [x] 4. Vérification
      - `venv\Scripts\python.exe manage.py check` ✅
      - `venv\Scripts\python.exe manage.py makemigrations --check` ✅
