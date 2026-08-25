# Déploiement OVH — Guide pas à pas (multi-clients)

Ce guide installe **un restaurant = une instance isolée** sur un seul VPS Ubuntu.
Chaque instance a : son code, sa base, ses médias, son domaine, son service.

---

## 1. Le serveur VPS

Chez OVH : commande un **VPS Value/Starter** (~5 €/mois) avec **Ubuntu 24.04**.
OVH t'envoie un email avec l'IP du serveur et le mot de passe root.

```bash
ssh root@IP_DU_SERVEUR
```

### Mise à jour et outils de base

```bash
apt update && apt upgrade -y
apt install -y git python3-venv python3-dev build-essential libpq-dev nginx curl
```

## 2. Redis et PostgreSQL (une seule fois pour tout le serveur)

```bash
apt install -y redis-server postgresql postgresql-contrib
systemctl enable --now redis-server postgresql
```

> Redis sert aux channels temps réel quand plusieurs processus tournent.
> PostgreSQL est plus robuste que SQLite en production.

## 3. Créer une instance par client

Exemple pour le premier client `moussa` :

```bash
adduser --disabled-password moussa
su - moussa
```

### 3.1 Code + environnement

```bash
git clone https://github.com/issa1299/gestion-restaurant-mono.git RestaurantPro
cd RestaurantPro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt psycopg2-binary gunicorn uvicorn
```

### 3.2 Base de données

Reviens sur root (`exit`) puis :

```bash
sudo -u postgres psql <<'SQL'
CREATE USER moussa WITH PASSWORD 'MOT_DE_PASSE_FORT';
CREATE DATABASE moussa_db OWNER moussa;
SQL
```

### 3.3 Fichier d'environnement

En tant que `moussa` :

```bash
nano ~/RestaurantPro/.env
```

Contenu :

```
SECRET_KEY=une-longue-chaine-aleatoire-generee
DJANGO_SETTINGS_MODULE=config.settings_prod
DJANGO_ALLOWED_HOSTS=chez-moussa.example.com
CSRF_TRUSTED_ORIGINS=https://chez-moussa.example.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=moussa_db
DB_USER=moussa
DB_PASSWORD=MOT_DE_PASSE_FORT
DB_HOST=127.0.0.1
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/1
```

Génère la SECRET_KEY : `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`

### 3.4 Migrer et préparer les fichiers

```bash
cd ~/RestaurantPro && source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 4. Service systemd (redémarre tout seul au reboot)

```bash
sudo nano /etc/systemd/system/moussa.service
```

```
[Unit]
Description=RestaurantPro - moussa (ASGI)
After=network.target redis-server.service postgresql.service

[Service]
User=moussa
Group=moussa
WorkingDirectory=/home/moussa/RestaurantPro
EnvironmentFile=/home/moussa/RestaurantPro/.env
ExecStart=/home/moussa/RestaurantPro/venv/bin/daphne \
    -b 127.0.0.1 -p 8001 config.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

> ⚠️ Chaque client a **son propre port** : moussa=8001, client2=8002, etc.

```bash
systemctl daemon-reload
systemctl enable --now moussa
systemctl status moussa
```

Daphne sert HTTP **et** WebSockets → notifications cuisine/dashboard fonctionnent.

## 5. Nginx (reverse proxy)

```bash
nano /etc/nginx/sites-available/moussa
```

```nginx
server {
    listen 80;
    server_name chez-moussa.example.com;

    client_max_body_size 20M;

    location /static/ {
        alias /home/moussa/RestaurantPro/staticfiles/;
    }
    location /media/ {
        alias /home/moussa/RestaurantPro/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        # WebSockets (notifications temps réel)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
ln -s /etc/nginx/sites-available/moussa /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

## 6. Domaine + HTTPS (OBLIGATOIRE)

1. Chez OVH : achète le domaine (~10 €/an) ou crée un sous-domaine gratuit
   (`moussa.tondomaine.com` pointant vers l'IP du VPS).
2. Attends la propagation DNS puis installe le certificat SSL :

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d chez-moussa.example.com
```

Renouvellement automatique inclus. **Sans HTTPS, la géolocalisation et
l'installation PWA ne fonctionnent pas** — c'est bloquant pour ton app.

## 7. Sauvegardes automatiques

```bash
mkdir -p /root/backups
nano /root/sauvegarde.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
for d in /home/*/RestaurantPro; do    # detection auto de tous les clients
    CLIENT=$(basename "$(dirname "$d")")
    DIR="$d"
    sudo -u postgres pg_dump ${CLIENT}_db | gzip > /root/backups/${CLIENT}_db_$DATE.sql.gz
    tar czf /root/backups/${CLIENT}_media_$DATE.tar.gz $DIR/media
done
find /root/backups -name "*.gz" -mtime +14 -delete   # garde 14 jours
```

```bash
chmod +x /root/sauvegarde.sh
crontab -e
# Ajoute : 0 3 * * * /root/sauvegarde.sh
```

## 8. Firewall simple

```bash
ufw allow OpenSSH
ufw allow "Nginx Full"
ufw enable
```

---

## Résumé : ajouter un nouveau client (automatique)

Le script `scripts/creer_client.sh` fait **tout** en une commande :

```bash
cd /root && git clone https://github.com/issa1299/gestion-restaurant-mono.git outils 2>/dev/null
cp outils/scripts/*.sh /root/ && chmod +x /root/*.sh

./creer_client.sh fatou chez-fatou.example.com
```

Il crée automatiquement : utilisateur Linux, code, venv, base PostgreSQL,
`.env` avec clé secrete unique, migrations, service systemd (port libre auto),
config Nginx, puis demande le compte administrateur.

**Ensuite il ne reste que :**
1. Pointer le domaine OVH vers l'IP du serveur
2. `certbot --nginx -d chez-fatou.example.com` (HTTPS)
3. Configurer l'identité du restaurant dans `/parametres/`
4. Ajouter la sauvegarde (auto-détectée par la boucle ci-dessus)

**Mettre à jour tous les clients** (détection automatique) :

```bash
./maj_instances.sh              # tous les clients installes
./maj_instances.sh moussa       # un seul client
```

Un petit VPS Value supporte facilement **5 à 10 restaurants**.

## Dépannage rapide

```bash
systemctl status moussa              # le service tourne ?
journalctl -u moussa -n 50           # dernières erreurs
tail -f /var/log/nginx/error.log     # erreurs nginx
nginx -t                             # config nginx valide ?
redis-cli ping                       # doit répondre PONG
```
