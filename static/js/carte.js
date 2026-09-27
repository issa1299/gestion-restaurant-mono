/* Helpers communs pour les cartes Leaflet (livraison détail + suivi client) */

function basculerPleinEcran(map) {
    const conteneur = map.getContainer();
    if (!document.fullscreenElement) {
        conteneur.requestFullscreen().catch(() => {});
    } else {
        document.exitFullscreen().catch(() => {});
    }
}

function ajouterControlePleinEcran(map) {
    L.Control.FullscreenCustom = L.Control.extend({
        options: { position: 'topright' },
        onAdd: function (map) {
            const btn = L.DomUtil.create('button', 'leaflet-bar leaflet-control leaflet-control-custom');
            btn.innerHTML = '<i class="fas fa-expand"></i>';
            btn.style.cssText = 'width:30px;height:30px;background:white;border:none;border-radius:4px;cursor:pointer;color:#334155;font-size:13px;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 5px rgba(0,0,0,0.4)';
            btn.title = 'Plein écran';
            btn.onclick = function (e) { L.DomEvent.stopPropagation(e); L.DomEvent.preventDefault(e); basculerPleinEcran(map); };
            return btn;
        }
    });
    map.addControl(new L.Control.FullscreenCustom());
}

function corrigerTailleCarte(map) {
    setTimeout(() => map.invalidateSize(), 300);
    window.addEventListener('resize', () => map.invalidateSize());
}

function formaterDistance(m) {
    const km = m / 1000;
    return km < 1 ? `${Math.round(m)} m` : `${km.toFixed(1)} km`;
}

function formaterDuree(s) {
    const min = Math.round(s / 60);
    if (min < 60) return `${min} min`;
    return `${Math.floor(min / 60)} h ${min % 60} min`;
}

function haversine(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/* Marqueurs style Google Maps */
function iconClientLeaflet(taille) {
    taille = taille || 36;
    return L.divIcon({
        html: `<div style="position:relative;width:${taille}px;height:${taille + 8}px">
            <div style="width:${taille}px;height:${taille}px;background:#EA4335;border:3px solid #fff;border-radius:50% 50% 50% 0;transform:rotate(-45deg);box-shadow:0 3px 10px rgba(0,0,0,.35)"></div>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-65%);width:${Math.round(taille*0.4)}px;height:${Math.round(taille*0.4)}px;background:#fff;border-radius:50%"></div>
        </div>`,
        iconSize: [taille, taille + 8],
        iconAnchor: [taille / 2, taille + 4],
        className: 'gm-marker'
    });
}

function iconLivreurLeaflet(taille) {
    taille = taille || 40;
    return L.divIcon({
        html: `<div style="width:${taille}px;height:${taille}px;background:#4285F4;border:3px solid #fff;border-radius:50%;box-shadow:0 3px 12px rgba(66,133,244,.45);display:flex;align-items:center;justify-content:center">
            <i class="fas fa-motorcycle" style="color:#fff;font-size:${Math.round(taille*0.42)}px"></i>
        </div>`,
        iconSize: [taille, taille],
        iconAnchor: [taille / 2, taille / 2],
        className: 'gm-marker'
    });
}

/* Polyline style Google Maps (bleu + bordure blanche) */
function tracerRouteGoogle(map, coords) {
    const bordure = L.polyline(coords, {
        color: '#fff', weight: 8, opacity: 0.9, lineCap: 'round', lineJoin: 'round'
    }).addTo(map);
    const ligne = L.polyline(coords, {
        color: '#4285F4', weight: 5, opacity: 1, lineCap: 'round', lineJoin: 'round'
    }).addTo(map);
    return { bordure: bordure, ligne: ligne };
}

/* ===== Fond de carte "routes" résilient =====
   Le serveur officiel OpenStreetMap bloque les applications qui ne
   respectent pas sa politique d'usage des tuiles (volume trop élevé,
   rechargements massifs sans cache, Referer filtré par un outil de
   « protection vie privée », etc.).
   PIÈGE IMPORTANT : OSM sert alors les tuiles avec un statut HTTP 200
   (le « 403 » fait partie de l'IMAGE elle-même) et la MÊME image pour
   toutes les coordonnées → ni « tileerror », ni « r.ok === false » ne
   permettent de détecter le blocage.
   Stratégie de détection : on télécharge 2 tuiles de coordonnées
   différentes et on compare leur contenu binaire — s'il est identique,
   le serveur est bloqué et on bascule sur le fournisseur suivant. */
const FOURNISSEURS_FOND = [
    {   // Esri World Street Map — rendu proche Google Maps, sans clé
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri'
    },
    {   // OpenStreetMap officiel
        url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    },
    {   // Miroir OSM Allemagne
        url: 'https://tile.openstreetmap.de/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    },
    {   // Esri World Imagery (satellite)
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri, Maxar'
    }
];

function remplacerJokersTuile(url, x, y) {
    return url
        .replace('{s}', 'a').replace('{r}', '')
        .replace('{z}', '7').replace('{x}', String(x)).replace('{y}', String(y));
}

function fetchAvecTimeout(url, ms) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), ms);
    return fetch(url, { cache: 'no-store', signal: ctrl.signal })
        .then(r => r.ok ? r.arrayBuffer() : Promise.reject(new Error('HTTP ' + r.status)))
        .finally(() => clearTimeout(timer));
}

function memeContenu(a, b) {
    if (a.byteLength !== b.byteLength) return false;
    const va = new Uint8Array(a), vb = new Uint8Array(b);
    const n = Math.min(256, va.length);
    for (let i = 0; i < n; i++) { if (va[i] !== vb[i]) return false; }
    return true;
}

/* Renvoie 'OK', 'BLOQUE' ou 'INCONNU' (réseau/CORS indisponible). */
async function sonderFournisseur(fournisseur) {
    try {
        const [a, b] = await Promise.all([
            fetchAvecTimeout(remplacerJokersTuile(fournisseur.url, 64, 42), 3000),
            fetchAvecTimeout(remplacerJokersTuile(fournisseur.url, 65, 42), 3000)
        ]);
        return memeContenu(a, b) ? 'BLOQUE' : 'OK';
    } catch (e) {
        return 'INCONNU';
    }
}

function creerCoucheFondResiliente(map, options) {
    options = options || {};
    const seuil = options.seuilErreurs || 6; // erreurs consécutives avant bascule
    let index = 0;
    let erreurs = 0;

    const couche = L.tileLayer(FOURNISSEURS_FOND[0].url, {
        maxZoom: options.maxZoom || 19,
        attribution: FOURNISSEURS_FOND[0].attribution
    });

    function appliquer(i) {
        index = i;
        const f = FOURNISSEURS_FOND[i];
        couche.setUrl(f.url, true);
        couche.options.attribution = f.attribution;
        // On repasse par remove/add pour que le contrôle d'attribution
        // affiché en bas de la carte soit mis à jour, puis on recharge.
        if (map.hasLayer(couche)) {
            map.removeLayer(couche);
            map.addLayer(couche);
        }
        console.warn('[carte] Fond de carte basculé vers :', f.url);
    }

    couche.on('tileload', () => { erreurs = 0; }); // le serveur répond → compteur à zéro
    couche.on('tileerror', () => {
        erreurs++;
        if (erreurs >= seuil && index < FOURNISSEURS_FOND.length - 1) {
            erreurs = 0;
            appliquer(index + 1);
        }
    });

    // Choix du fournisseur AVANT d'afficher la couche (voir commentaire
    // du bloc FOURNISSEURS_FOND pour la détection du blocage OSM).
    (async () => {
        let choix = 0;
        for (let i = 0; i < FOURNISSEURS_FOND.length; i++) {
            const etat = await sonderFournisseur(FOURNISSEURS_FOND[i]);
            if (etat === 'OK') { choix = i; break; }
            if (etat === 'BLOQUE') {
                console.warn('[carte] Serveur de tuiles bloqué :', FOURNISSEURS_FOND[i].url);
                choix = Math.min(i + 1, FOURNISSEURS_FOND.length - 1);
                continue; // on teste le fournisseur suivant
            }
            break; // INCONNU (réseau/CORS) → on garde ce fournisseur
        }
        if (choix !== 0) appliquer(choix);
        couche.addTo(map);
    })();

    return couche; // objet stable : utilisable tel quel dans L.control.layers
}