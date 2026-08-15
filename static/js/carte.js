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

function iconClientLeaflet(taille) {
    taille = taille || 24;
    return L.divIcon({
        html: `<div style="background:#f97316;border:3px solid white;border-radius:50% 50% 50% 0;transform:rotate(-45deg);width:${taille}px;height:${taille}px;box-shadow:0 2px 8px rgba(0,0,0,0.3)"></div>`,
        iconSize: [taille, taille], iconAnchor: [taille / 2, taille], className: ''
    });
}

function iconLivreurLeaflet(taille) {
    taille = taille || 24;
    return L.divIcon({
        html: `<div style="background:#3b82f6;border:3px solid white;border-radius:50%;width:${taille}px;height:${taille}px;box-shadow:0 2px 8px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center"><i class="fas fa-motorcycle" style="color:white;font-size:${Math.round(taille / 2)}px"></i></div>`,
        iconSize: [taille, taille], iconAnchor: [taille / 2, taille / 2], className: ''
    });
}