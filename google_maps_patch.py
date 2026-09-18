import re

with open('templates/lavraison/detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacement du marqueur client
old_marker_client = """// Marqueur client (fixe)
    let clientMarkerLiv = null;
    if (clientLat && clientLng) {
        clientMarkerLiv = L.marker([clientLat, clientLng], { icon: iconClientLiv })
            .addTo(mapLivraison).bindPopup('<b>🏠 Client</b>').openPopup();
    }"""

new_marker_client = """// Marqueur client (fixe)
    let clientMarkerLiv = null;
    if (clientLat && clientLng) {
        clientMarkerLiv = L.marker([clientLat, clientLng], { icon: iconClientGoogle })
            .addTo(mapLivraison).bindPopup('<b>🏠 Client</b>').openPopup();
    }"""

if old_marker_client in content:
    content = content.replace(old_marker_client, new_marker_client)
    print("✓ Remplacement marker client réussi")
else:
    print("✗ Pattern marker client non trouvé")

# Remplacement marqueur livreur dans updateMarker
old_updateMarker = """function updateMarker(lat, lng) {
        if (!lat || !lng) return;
        if (!markerLivraison) {
            markerLivraison = L.marker([lat, lng], { icon: iconLivreurLiv })
                .addTo(mapLivraison).bindPopup('<b>🛵 Vous</b>');
        } else {
            deplacerEnDouceur(markerLivraison, lat, lng);
        }
        chargerRouteLiv(lat, lng);
    }"""

new_updateMarker = """function updateMarker(lat, lng, heading = null) {
        if (!lat || !lng) return;
        if (!markerLivraison) {
            markerLivraison = L.marker([lat, lng], { icon: iconLivreurGoogle })
                .addTo(mapLivraison).bindPopup('<b>🛵 Vous</b>');
            // Fixer l'orientation initiale à 0
            rotateMarker(markerLivraison, 0);
        } else {
            // Animation fluide entre deux positions
            deplacerEnDouceur(markerLivraison, lat, lng);
            // Faire tourner le marqueur selon l'orientation fournie
            if (heading !== null) {
                rotateMarker(markerLivraison, heading);
            }
        }
        chargerRouteLiv(lat, lng);
        // Animation flyTo fluide
        flyToMarker(lat, lng);
    }"""

if old_updateMarker in content:
    content = content.replace(old_updateMarker, new_updateMarker)
    print("✓ Remplacement updateMarker réussi")
else:
    print("✗ Pattern updateMarker non trouvé")

# Write the modified content back
with open('templates/lavraison/detail.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("✓ Fichier mis à jour")