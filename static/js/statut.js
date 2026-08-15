/* Fonction générique de changement de statut (commandes, cuisine, livraison)
 * Usage : changerStatutAction(url, statut, { id, btn, onSuccess, reload })
 */
function changerStatutAction(url, statut, options = {}) {
    const btn = options.btn || null;
    const texteOriginal = btn ? btn.innerHTML : '';
    const csrf = options.csrf || getCSRFToken();

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> En cours...';
    }

    const formData = new FormData();
    formData.append('statut', statut);
    formData.append('csrfmiddlewaretoken', csrf);

    fetch(url, {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (typeof options.onSuccess === 'function') {
                    options.onSuccess(data, btn);
                } else if (options.reload !== false) {
                    window.location.reload();
                }
            } else {
                alert(data.error || 'Erreur lors du changement de statut');
                if (btn) { btn.disabled = false; btn.innerHTML = texteOriginal; }
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur de connexion. Veuillez réessayer.');
            if (btn) { btn.disabled = false; btn.innerHTML = texteOriginal; }
        });
}

function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}
