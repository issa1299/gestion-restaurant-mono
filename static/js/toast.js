/* Notifications toast + confirmation stylées (remplace alert/confirm) */

function afficherToast(message, type) {
    type = type || 'info';
    const couleurs = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'warning': 'bg-yellow-500',
        'info': 'bg-blue-500'
    };
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 space-y-2 z-[200]';
        document.body.appendChild(container);
    }
    const notif = document.createElement('div');
    notif.className = `${couleurs[type]} text-white px-5 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-3 max-w-xs`;
    notif.innerHTML = message;
    container.appendChild(notif);
    setTimeout(() => {
        notif.style.transition = '0.5s';
        notif.style.opacity = '0';
        notif.style.transform = 'translateX(120px)';
        setTimeout(() => notif.remove(), 500);
    }, 4000);
}

function confirmerAction(message, options) {
    options = options || {};
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.id = 'confirm-overlay';
        overlay.className = 'fixed inset-0 z-[200] flex items-center justify-center p-4';
        overlay.innerHTML = `
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
            <div class="relative bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
                <div class="w-12 h-12 mx-auto rounded-full bg-orange-50 text-orange-500 flex items-center justify-center mb-4">
                    <i class="fas fa-triangle-exclamation text-xl"></i>
                </div>
                <p class="text-center text-slate-800 font-semibold mb-6">${message}</p>
                <div class="flex gap-3">
                    <button type="button" class="btn-confirm-cancel flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-2.5 rounded-xl transition">
                        ${options.cancelText || 'Annuler'}
                    </button>
                    <button type="button" class="btn-confirm-ok flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold py-2.5 rounded-xl transition">
                        ${options.okText || 'Confirmer'}
                    </button>
                </div>
            </div>
        `;
        overlay.querySelector('.absolute').addEventListener('click', () => fermer(false));
        overlay.querySelector('.btn-confirm-cancel').addEventListener('click', () => fermer(false));
        overlay.querySelector('.btn-confirm-ok').addEventListener('click', () => fermer(true));
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fermer(false); }, { once: true });

        function fermer(ok) {
            overlay.remove();
            document.removeEventListener('keydown', () => {});
            resolve(ok);
        }

        document.body.appendChild(overlay);
    });
}