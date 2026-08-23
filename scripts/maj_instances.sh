#!/bin/bash
# ============================================================
# RestaurantPro - Mise a jour automatique de toutes les instances
# A executer en root :  ./maj_instances.sh [client1 client2 ...]
# Sans argument, met a jour tous les clients listes dans CLIENTS.
# ============================================================

CLIENTS=("moussa")   # <-- ajouter les nouveaux clients ici : ("moussa" "client2")
BRANCHE="mono"

if [ "$#" -gt 0 ]; then
    CLIENTS=("$@")
fi

LOG=/var/log/restaurantpro-maj.log

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

for CLIENT in "${CLIENTS[@]}"; do
    DIR="/home/$CLIENT/RestaurantPro"
    SERVICE="$CLIENT"

    log "===== Mise a jour de $CLIENT ====="

    if [ ! -d "$DIR" ]; then
        log "ERREUR: $DIR introuvable, ignore."
        continue
    fi

    cd "$DIR" || { log "ERREUR: impossible d'entrer dans $DIR"; continue; }

    # Recuperation du code (origin-mono sur ce depot, sinon origin)
    if git remote get-url origin-mono >/dev/null 2>&1; then
        REMOTE_NAME="origin-mono"
    else
        REMOTE_NAME="origin"
    fi
    git fetch "$REMOTE_NAME" "$BRANCHE" >>"$LOG" 2>&1 || { log "ERREUR: git fetch"; continue; }

    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "$REMOTE_NAME/$BRANCHE")
    if [ "$LOCAL" = "$REMOTE" ]; then
        log "$CLIENT deja a jour ($LOCAL)"
    else
        log "$CLIENT : mise a jour $LOCAL -> $REMOTE"
        git reset --hard "$REMOTE_NAME/$BRANCHE" >>"$LOG" 2>&1 || { log "ERREUR: git reset"; continue; }

        # Dependances (au cas ou requirements.txt a change)
        "$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt" >>"$LOG" 2>&1 \
            || log "ATTENTION: pip install a echoue"

        # Migrations + fichiers statiques
        chown "$CLIENT:$CLIENT" "$DIR/.env" >/dev/null 2>&1
        sudo -u "$CLIENT" bash -c "cd $DIR && source venv/bin/activate && set -a && source .env && set +a && python manage.py migrate --noinput && python manage.py collectstatic --noinput" >>"$LOG" 2>&1 \
            || { log "ERREUR: migrate/collectstatic, service NON redemarre"; continue; }

        # Redemarrage du service
        systemctl restart "$SERVICE" && log "$CLIENT redemarre : OK" || log "ERREUR: restart $SERVICE"
    fi
done

log "===== Fin des mises a jour ====="
