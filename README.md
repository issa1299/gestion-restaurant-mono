# RestaurantPro Mono

Application de gestion complète pour restaurant : ventes au comptoir (POS), gestion de tables, menu, commandes, cuisine, livraison, clients, fournisseurs, stock, rapports et paramètres.

## Technologies

- Django 6.0.7
- Channels 4.3 (WebSockets, temps réel — optionnel)
- Daphne (serveur ASGI)
- SQLite (base de données)
- WhiteNoise (fichiers statiques)
- Tailwind CSS via CDN
- Leaflet (cartes de livraison)
- DataTables (tableaux — chargé uniquement sur la page clients)

## Installation (local)

```bash
# 1. Cloner le dépôt
git clone git@github.com:issa1299/gestion-restaurant-mono.git
cd gestion-restaurant-mono

# 2. Créer l'environnement virtuel
python -m venv venv

# 3. Activer et installer les dépendances
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt

# 4. Migrations et utilisateur admin
python manage.py migrate
python manage.py createsuperuser

# 5. Lancer le serveur de développement
python manage.py runserver 0.0.0.0:8080
```

Ou via le script fourni (daphne, port 8001) :

```bat
demarrer_serveur.bat
```

## Rôles utilisateurs

| Rôle       | Description           |
|------------|-----------------------|
| ADMIN      | Administrateur        |
| GERANT     | Gérant                |
| CAISSIER   | Caissier              |
| SERVEUR    | Serveur               |
| CUISINIER  | Cuisinier             |
| LIVREUR    | Livreur               |
| VENDEUR    | Vendeur               |
| CLIENT     | Client (portail en ligne) |

## Structure des applications

| App           | Rôle                                              |
|---------------|---------------------------------------------------|
| accounts      | Utilisateurs, rôles, authentification             |
| dashboard     | Tableau de bord                                   |
| restaurant    | POS (point de vente), commande en ligne           |
| tables        | Gestion des tables                                |
| menu          | Produits et catégories du menu                    |
| commandes     | Commandes (création, statuts)                     |
| cuisine       | File d'attente cuisine                            |
| stock         | Suivi de stock (désactivé, données conservées)    |
| fournisseurs  | Fournisseurs et approvisionnements                |
| livraison     | Livraisons, suivi GPS en temps réel               |
| clients       | Fiches clients                                    |
| notifications | Notifications en temps réel                       |
| rapports      | Rapports et statistiques                          |
| parametres    | Paramètres du restaurant                          |
| ventes        | Historique des ventes, tickets                    |

## Déploiement sur PythonAnywhere

1. Clonez le dépôt sur `/home/<utilisateur>/RestaurantPro-Mono`.
2. Créez un venv : `/home/<utilisateur>/.virtualenvs/monoenv` (Python 3.12) puis `pip install -r requirements.txt`.
3. Définissez les variables d'environnement (onglet **Web** > **Environment variables**) :
   - `DJANGO_SETTINGS_MODULE` = `config.settings_prod`
   - `SECRET_KEY` = une clé secrète aléatoire (**obligatoire**, l'app refuse de démarrer sans)
4. Mettre à jour le WSGI avec le contenu de `pythonanywhere_wsgi.py`.
5. `python manage.py migrate` (avec le venv), puis **Reload**.

> **Note** : le plan gratuit de PythonAnywhere ne gère pas les WebSockets. L'app fonctionne en WSGI et ignore silencieusement le temps réel.

## Mise à jour (déploiement)

```bash
# Sur PythonAnywhere
cd ~/RestaurantPro-Mono
git pull origin-mono mono
# puis cliquer sur "Reload" dans l'onglet Web
```

## Commandes utiles

```bash
python manage.py check
python manage.py test                    # tous les tests
python manage.py test apps.commandes     # tests d'une app
python manage.py collectstatic           # statiques de production
```

## Configuration

- Développement : `config/settings.py` (DEBUG actif, cache LocMem)
- Production : `config/settings_prod.py` (DEBUG inactif, sécurité renforcée, SECRET_KEY via environnement)