#!/bin/bash
# ============================================================
# RestaurantPro - Mise a jour automatique de TOUTES les instances
#
# Detecte automatiquement les clients (dossiers /home/*/RestaurantPro).
#
# Usage (en root) :
#   ./maj_instances.sh                -> met a jour tous les clients
#   ./maj_instances.sh moussa fatou   -> met a jour seulement ceux-la
# ============================================================

BRANCHE="mono"
LOG=/var/log/restaurantpro-maj.log

COULEUR_VERT='\033[0;32m'; COULEUR_ROUGE='\033[0;31m'; COULEUR_JAUNE='\033[1;33m'; FIN='\033[0m'
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

# Detection auto des clients installes, sauf si passes en argument
if [ "$#" -gt 0 ]; then
    CLIENTS=("$@")
else
    CLIENTS=()
    for d in /home/*/RestaurantPro; do
        [ -d "$d" ] && CLIENTS+=("$(basename "$(dirname "$d")")")
    done
fi

[ ${#CLIENTS[@]} -eq 0 ] && { echo "Aucune instance trouvee dans /home/*/RestaurantPro"; exit 1; }

log "===== Mise a jour de ${#CLIENTS[@]} instance(s) : ${CLIENTS[*]} ====="

NB_OK=0; NB_DEJA=0; NB_KO=0

for CLIENT in "${CLIENTS[@]}"; do
    DIR="/home/$CLIENT/RestaurantPro"

    if [ ! -d "$DIR" ]; then
        log "[ERREUR] $DIR introuvable, ignore."
        NB_KO=$((NB_KO+1))
        continue
    fi

    cd "$DIR" || { log "[ERREUR] impossible d'entrer dans $DIR"; NB_KO=$((NB_KO+1)); continue; }

    # Remote : origin-mono si present sinon origin
    if git remote get-url origin-mono >/dev/null 2>&1; then
        REMOTE_NAME="origin-mono"
    else
        REMOTE_NAME="origin"
    fi

    git fetch "$REMOTE_NAME" "$BRANCHE" >>"$LOG" 2>&1 || { log "[ERREUR] git fetch $CLIENT"; NB_KO=$((NB_KO+1)); continue; }

    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "$REMOTE_NAME/$BRANCHE")

    if [ "$LOCAL" = "$REMOTE" ]; then
        log "[DEJA A JOUR] $CLIENT ($LOCAL)"
        NB_DEJA=$((NB_DEJA+1))
        continue
    fi

    log "[MAJ] $CLIENT : $LOCAL -> $REMOTE"

    # Dependances (si requirements.txt a change)
    "$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt" >>"$LOG" 2>&1 \
        || log "[ATTENTION] pip install $CLIENT a echoue"

    # Migrations + statiques avec les variables du .env
    sudo -u "$CLIENT" bash -c "cd '$DIR' && set -a && source .env && set +a && venv/bin/python manage.py migrate --noinput && venv/bin/python manage.py collectstatic --noinput" >>"$LOG" 2>&1 \
        || { log "[ERREUR] migrate/collectstatic $CLIENT - service NON redemarre (ancienne version conservée)"; NB_KO=$((NB_KO+1)); continue; }

    systemctl restart "$CLIENT" \
        && { log "[OK] $CLIENT redemarre"; NB_OK=$((NB_OK+1)); } \
        || { log "[ERREUR] restart $CLIENT"; NB_KO=$((NB_KO+1)); }
done

echo ""
echo -e "${COULEUR_JAUNE}===== Resume =====${FIN}"
echo -e "${COULEUR_VERT}Mises a jour : $NB_OK${FIN} | Deja a jour : $NB_DEJA | Echecs : $NB_KO"
log "===== Fin : OK=$NB_OK deja-a-jour=$NB_DEJA echecs=$NB_KO ====="
