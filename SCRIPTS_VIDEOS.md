# Scripts des vidéos explicatives — RestaurantPro

Guide complet pour tourner vos vidéos : durée, préparation, scènes
(ce que vous faites à l'écran / ce que vous dites).

---

## Préparation commune (avant tout tournage)

1. Lancer le serveur : `python manage.py runserver` → http://127.0.0.1:8000/
2. Données réalistes dans l'app :
   - Catégories : Plats, Grillades, Boissons, Desserts
   - Produits avec prix FCFA : Poulet braise 5 000, Alloco 1 500, Attiéké poisson 3 500, Jus de bissap 1 000...
   - 3-4 tables créées
   - Logo + nom « Chez Moussa » dans Paramètres
3. OBS Studio réglé : 1920×1080, 30 fps, micro testé
4. Navigateur en plein écran (F11), zoom 100 %, favoris fermés
5. Pour la vidéo temps réel : deux fenêtres côte à côte (client à gauche, cuisine/caisse à droite)

> Parlez lentement, phrases courtes. Si vous vous trompez, gardez le calme :
> marquez une pause de 2 secondes et reprenez la phrase (facile à couper au montage).

---

## VIDÉO 1 — DÉMO GLOBALE (la vidéo qui vend) · 2 min 30

**Objectif** : donner envie au gérant. Montrer le parcours complet sans détail technique.

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Page d'accueil du site, léger scroll | « Voici le site de votre restaurant. Vos clients y voient vos plats, vos photos, et peuvent commander directement depuis leur téléphone. » |
| 0:20 | Cliquer sur « Commander », faire défiler les plats | « Le menu est toujours à jour : vous le gérez vous-même en quelques clics. » |
| 0:35 | Ajouter 2-3 plats au panier, ouvrir le panier | « Le client choisit ses plats et valide sa commande. » |
| 0:45 | Remplir nom, téléphone, adresse ; cliquer « Me localiser » | « Il indique son adresse — il peut même se localiser automatiquement pour la livraison. » |
| 1:00 | Valider → page de confirmation avec le suivi | « La commande arrive instantanément en cuisine. » |
| 1:10 | Basculer sur la fenêtre CUISINE : la commande apparaît | « Ici, la cuisine voit la nouvelle commande en direct, avec une notification. » |
| 1:25 | Cliquer « Démarrer », puis « Marquer prête » | « Le cuisinier suit l'avancement en un clic. » |
| 1:40 | Basculer sur la CAISSE : sélectionner la commande, encaisser | « Au moment de payer, le caissier encaisse : espèces, Orange Money, Wave ou carte, avec remise si besoin. » |
| 1:55 | Ticket affiché → taper un numéro → bouton WhatsApp | « Et le ticket part directement sur le WhatsApp du client. Professionnel, non ? » |
| 2:10 | Dashboard : chiffre d'affaires du jour | « De son côté, le gérant suit le chiffre d'affaires en temps réel, les meilleures ventes, les réservations... » |
| 2:20 | Écran final (logo + votre contact) | « RestaurantPro : votre restaurant, modernisé. Contactez-moi pour la démonstration chez vous. » |

---

## VIDÉO 2 — COMMANDE EN LIGNE VUE CLIENT · 1 min

**Objectif** : rassurer — « mes clients sauront utiliser ». Filmer idéalement sur **téléphone**.

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Téléphone : ouverture du site | « Voici comment vos clients commandent, directement depuis leur téléphone. » |
| 0:08 | Parcourir le menu, ajouter un plat | « On choisit ses plats comme sur n'importe quelle app de livraison. » |
| 0:20 | Ouvrir le panier, valider | « Le panier affiche le total immédiatement. » |
| 0:30 | Nom, téléphone, adresse, localisation, valider | « Nom, numéro, adresse — la position GPS peut être détectée automatiquement. » |
| 0:45 | Page de confirmation avec le numéro de commande | « Et voilà ! Le client reçoit son ticket, peut-être même par email, et suit l'état de sa commande en direct. » |
| 0:55 | Logo final | « Simple pour vos clients, puissant pour vous. » |

---

## VIDÉO 3 — FORMATION CAISSE (POS) · 3 min

**Objectif** : le caissier doit être autonome après visionnage.

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Connexion caissier → tableau de bord | « Bienvenue. Connectez-vous avec votre compte caissier. » |
| 0:15 | Ouvrir « Ventes » (POS) | « Voici votre caisse. À gauche, tous les produits classés par catégorie. » |
| 0:30 | Ajouter plusieurs produits, montrer les quantités | « Touchez un produit pour l'ajouter. Les quantités se règlent ici. » |
| 0:50 | Choisir le type : Sur place / Table 3 | « Sur place ? Sélectionnez la table. À emporter ou livraison, c'est ici aussi. » |
| 1:05 | Appliquer une remise 10 % | « Pour une remise, tapez le pourcentage : le total recalcule tout seul. » |
| 1:20 | Encaisser en Orange Money, saisir montant reçu → monnaie rendue | « Choisissez le mode de paiement. Si le client paie 10 000 pour 7 500, la monnaie s'affiche automatiquement. » |
| 1:50 | Ticket imprimable qui apparaît | « Le ticket s'affiche prêt à imprimer. » |
| 2:05 | Taper le numéro du client → Envoyer par WhatsApp | « Vous pouvez aussi envoyer le reçu sur le WhatsApp du client : propre et rapide. » |
| 2:20 | Historique des ventes : filtres, recherche, détail | « Toutes les ventes sont archivées : recherche par date, caissier, mode de paiement. » |
| 2:40 | Annulation d'une vente (motif demandé) | « Une erreur ? Une vente peut être annulée, c'est tracé et visible par le gérant. » |
| 2:55 | Fin | « Voilà, vous savez encaisser ! » |

---

## VIDÉO 4 — FORMATION CUISINE · 1 min 30

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Connexion cuisinier → écran cuisine | « L'écran de la cuisine. Rien à installer : ça marche sur tablette ou téléphone. » |
| 0:15 | Une commande arrive (déclenchée depuis un autre appareil) avec le son | « Nouvelle commande : notification immédiate dès qu'un client ou un serveur valide. » |
| 0:35 | Lire la commande : table, plats, quantités | « Table, plats, quantités : tout est lisible d'un coup d'œil. » |
| 0:45 | « Démarrer la préparation » puis « Marquer prête » | « Un bouton pour lancer la préparation, un autre quand c'est prêt. Le serveur est prévenu automatiquement. » |
| 1:15 | Fin | « Plus de papier, plus de cris entre salle et cuisine. » |

---

## VIDÉO 5 — AJOUTER UN PLAT AVEC PHOTO (téléphone) · 1 min 30

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Téléphone : Menu → Ajouter un produit | « Ajouter un plat ? Prenez votre téléphone. » |
| 0:15 | Remplir nom « Poulet braise », prix « 5000 », catégorie | « Nom, prix, catégorie. » |
| 0:30 | Bouton « Prendre une photo » → la caméra s'ouvre, photographier un plat réel | « Photographiez le plat directement : pas besoin d'ordinateur ni de retouche. » |
| 0:50 | Aperçu de la photo, enregistrer | « Vérifiez l'aperçu, enregistrez. » |
| 1:05 | Le plat apparaît sur le site public | « Et le plat est déjà visible par vos clients sur le site. » |
| 1:20 | Fin | « Votre menu reste toujours à jour, même pendant le service. » |

---

## VIDÉO 6 — RÉSERVATIONS & MESSAGES · 1 min 30

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Site public → page Réserver → remplir le formulaire | « Vos clients réservent leur table en ligne : nom, date, heure, nombre de personnes. » |
| 0:25 | Dashboard : notification de réservation | « La demande tombe directement sur votre tableau de bord. » |
| 0:40 | Réservations → cliquer « Confirmer » | « Vous confirmez d'un clic... » |
| 0:55 | Montrer l'email de confirmation reçu (boîte mail) | « ...et le client reçoit automatiquement cet email de confirmation. S'il laisse son email, bien sûr. » |
| 1:10 | Messages de contact → répondre | « Les messages via le site arrivent ici, et vous pouvez répondre par email. » |
| 1:25 | Fin | « Votre salle se remplit toute seule. » |

---

## VIDÉO 7 — STOCK & RAPPORTS (pour le gérant) · 2 min

| Temps | À l'écran | Vous dites |
|---|---|---|
| 0:00 | Dashboard gérant : CA du jour, graphique 7 jours | « Votre tableau de bord : chiffre d'affaires du jour et tendance de la semaine. » |
| 0:20 | Rapports : choisir période, top des ventes | « Les rapports par période : quels plats marchent le mieux, quel jour est le plus fort. » |
| 0:45 | Export CSV (ouvrir dans Excel) | « Exportez tout en Excel si votre comptable préfère. » |
| 1:00 | Stock : liste, mouvement entrée | « Le stock : à chaque livraison de marchandises, enregistrez l'entrée. » |
| 1:20 | Mouvement sortie lié à une vente | « Les ventes sortent automatiquement du stock. » |
| 1:40 | Historique des mouvements | « Tout est tracé : qui a entré quoi, quand. » |
| 1:55 | Fin : « Vous pilotez votre restaurant avec des chiffres, pas au flair. » |

---

## Après le tournage

1. Montage CapCut : couper les hésitations, ajouter des titres aux étapes (« 1. Ajoutez au panier »)
2. Musique douce à 10 % de volume maximum
3. Exporter en 1080p, uploader sur **YouTube en « non répertorié »**
4. Créer une playlist « Formation RestaurantPro »
5. Envoyer les liens par WhatsApp aux clients + intégrer dans votre offre commerciale

## Matériel minimal

- Micro-cravate (~10 000 FCFA) : le son compte plus que l'image
- Tourner le matin (lumière), téléphone posé stable pour la partie mobile
