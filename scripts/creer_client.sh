#!/bin/bash
# ============================================================
# RestaurantPro - Installation automatique d'un nouveau restaurant
#
# Usage (en root) :
#   ./creer_client.sh <nom_client> <domaine>
# Exemple :
#   ./creer_client.sh fatou chez-fatou.example.com
#
# Le script cree : utilisateur Linux, code, venv, base PostgreSQL,
# fichier .env, migrations, service systemd (port auto), config Nginx.
# SSL : lancez ensuite certbot quand le domaine pointe vers le serveur.
# ============================================================

set -euo pipefail

COULEUR_VERT='\033[0;32m'; COULEUR_ROUGE='\033[0;31m'; COULEUR_JAUNE='\033[1;33m'; FIN='\033[0m'
ok()      { echo -e "${COULEUR_VERT}[OK]${FIN} $1"; }
erreur()  { echo -e "${COULEUR_ROUGE}[ERREUR]${FIN} $1" >&2; exit 1; }
etape()   { echo -e "\n${COULEUR_JAUNE}==>${FIN} $1"; }

REPO="https://github.com/issa1299/gestion-restaurant-mono.git"
BRANCHE="mono"
PORT_BASE=8000

[[ $# -eq 2 ]] || erreur "Usage : ./creer_client.sh <nom_client> <domaine>   (ex : ./creer_client.sh fatou chez-fatou.exemple.com)"
CLIENT="$1"
DOMAIN="$2"

[[ $CLIENT =~ ^[a-z0-9_-]+$ ]] || erreur "Nom client invalide (lettres minuscules, chiffres, - _ uniquement)"
id "$CLIENT" &>/dev/null && erreur "L'utilisateur $CLIENT existe deja"
[[ $DOMAIN =~ ^[a-z0-9.-]+\.[a-z]{2,}$ ]] || erreur "Domaine invalide : $DOMAIN"

echo "=============================================="
echo " RestaurantPro - Installation de : $CLIENT"
echo " Domaine : $DOMAIN"
echo "=============================================="

# ------------------------------------------------------------
etape "1/8 Utilisateur Linux"
adduser --disabled-password --gecos "" "$CLIENT"
ok "Utilisateur $CLIENT cree"

# ------------------------------------------------------------
etape "2/8 Code source + environnement Python"
su - "$CLIENT" -c "
    git clone -b $BRANCHE $REPO RestaurantPro >/dev/null 2>&1
    cd ~/RestaurantPro
    python3 -m venv venv
    venv/bin/pip install -q --upgrade pip
    venv/bin/pip install -q -r requirements.txt psycopg2-binary
"
ok "Code clone et dependances installees"

# ------------------------------------------------------------
etape "3/8 Base de donnees PostgreSQL"
DB_NAME="${CLIENT}_db"
DB_USER="$CLIENT"
DB_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
sudo -u postgres psql -v ON_ERROR_STOP=1 >/dev/null <<SQL
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
SQL
ok "Base $DB_NAME creee"

# ------------------------------------------------------------
etape "4/8 Fichier d'environnement (.env)"
SECRET_KEY=$(openssl rand -base64 50 | tr -dc 'a-zA-Z0-9!@#%^&*(-_=+)' | head -c 50)
ENV_FILE="/home/$CLIENT/RestaurantPro/.env"
cat > "$ENV_FILE" <<EOF
SECRET_KEY=$SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings_prod
DJANGO_ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
DB_ENGINE=django.db.backends.postgresql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_HOST=127.0.0.1
DB_PORT=5432
EOF
chown "$CLIENT:$CLIENT" "$ENV_FILE"
chmod 600 "$ENV_FILE"
ok ".env genere (cle secrete unique)"

# ------------------------------------------------------------
etape "5/8 Migrations + fichiers statiques"
su - "$CLIENT" -c "
    cd ~/RestaurantPro
    set -a && source .env && set +a
    venv/bin/python manage.py migrate --noinput >/dev/null
    venv/bin/python manage.py collectstatic --noinput >/dev/null
"
ok "Base initialisee"

# Compte administrateur (interactif)
echo -e "${COULEUR_JAUNE}--> Creation du compte administrateur du restaurant${FIN}"
su - "$CLIENT" -c "
    cd ~/RestaurantPro
    set -a && source .env && set +a
    venv/bin/python manage.py createsuperuser
"

# ------------------------------------------------------------
etape "6/8 Service systemd (recherche du port libre)"
PORT=$PORT_BASE
while ss -tlnp | grep -q ":$PORT "; do
    PORT=$((PORT + 1))
done
cat > "/etc/systemd/system/$CLIENT.service" <<EOF
[Unit]
Description=RestaurantPro - $CLIENT (ASGI)
After=network.target redis-server.service postgresql.service

[Service]
User=$CLIENT
Group=$CLIENT
WorkingDirectory=/home/$CLIENT/RestaurantPro
EnvironmentFile=/home/$CLIENT/RestaurantPro/.env
ExecStart=/home/$CLIENT/RestaurantPro/venv/bin/daphne -b 127.0.0.1 -p $PORT config.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now "$CLIENT" >/dev/null 2>&1
sleep 2
systemctl is-active --quiet "$CLIENT" || erreur "Le service $CLIENT ne demarre pas (voir journalctl -u $CLIENT)"
ok "Service $CLIENT actif sur le port $PORT"

# ------------------------------------------------------------
etape "7/8 Configuration Nginx"
NGINX_FILE="/etc/nginx/sites-available/$CLIENT"
cat > "$NGINX_FILE" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    client_max_body_size 20M;

    location /static/ {
        alias /home/$CLIENT/RestaurantPro/staticfiles/;
    }
    location /media/ {
        alias /home/$CLIENT/RestaurantPro/media/;
    }
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }
}
EOF
ln -sf "$NGINX_FILE" "/etc/nginx/sites-enabled/$CLIENT"
nginx -t >/dev/null 2>&1 || erreur "Configuration Nginx invalide"
systemctl reload nginx
ok "Nginx configure pour $DOMAIN"

# ------------------------------------------------------------
etape "8/8 Resume"
echo ""
echo "=============================================="
echo -e " ${COULEUR_VERT}Installation terminee !${FIN}"
echo "----------------------------------------------"
echo " Client      : $CLIENT"
echo " Domaine     : https://$DOMAIN"
echo " Port interne: $PORT"
echo " Base        : $DB_NAME (mot de passe dans .env)"
echo " Service     : systemctl status $CLIENT"
echo "----------------------------------------------"
echo " PROCHAINES ETAPES :"
echo "  1. Chez OVH : faire pointer $DOMAIN vers l'IP de ce serveur"
echo "  2. Attendre la propagation DNS puis lancer :"
echo "       certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "  3. Ouvrir https://$DOMAIN/parametres/ : nom, logo, WhatsApp..."
echo "  4. Ajouter le client aux sauvegardes (/root/sauvegarde.sh)"
echo "=============================================="
