/**
 * Mode hors-ligne RestaurantPro
 * - Bandeau visible si pas de réseau
 * - File d'attente des actions livreur (statut) pour envoi au retour du réseau
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'rp_offline_queue';
  var BANNER_ID = 'rp-offline-banner';

  function isOnline() {
    return navigator.onLine !== false;
  }

  function getQueue() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function saveQueue(q) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(q));
    } catch (e) {}
  }

  /** Ajoute une action à envoyer plus tard (ex: changement statut livraison) */
  window.queueOfflineAction = function (action) {
    // action = { url, method, body, headers, label }
    var q = getQueue();
    action.id = Date.now() + '-' + Math.random().toString(36).slice(2, 8);
    action.createdAt = new Date().toISOString();
    q.push(action);
    saveQueue(q);
    updateBanner();
    if (typeof afficherToast === 'function') {
      afficherToast('Hors ligne — action enregistrée, envoi dès le retour du réseau', 'info');
    }
    return action.id;
  };

  function getCsrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  async function flushQueue() {
    if (!isOnline()) return;
    var q = getQueue();
    if (!q.length) return;

    var remaining = [];
    for (var i = 0; i < q.length; i++) {
      var item = q[i];
      try {
        var headers = Object.assign(
          { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
          item.headers || {}
        );
        if (item.body && typeof item.body === 'object' && !headers['Content-Type']) {
          headers['Content-Type'] = 'application/json';
        }
        var res = await fetch(item.url, {
          method: item.method || 'POST',
          headers: headers,
          body: typeof item.body === 'string' ? item.body : JSON.stringify(item.body || {}),
        });
        if (!res.ok) remaining.push(item);
      } catch (e) {
        remaining.push(item);
      }
    }
    saveQueue(remaining);
    updateBanner();
    if (q.length && remaining.length < q.length && typeof afficherToast === 'function') {
      afficherToast('Actions hors-ligne synchronisées', 'success');
    }
  }

  function ensureBanner() {
    var el = document.getElementById(BANNER_ID);
    if (el) return el;
    el = document.createElement('div');
    el.id = BANNER_ID;
    el.setAttribute('role', 'status');
    el.style.cssText =
      'display:none;position:fixed;top:0;left:0;right:0;z-index:10000;' +
      'background:#0f172a;color:#fff;text-align:center;padding:10px 12px;' +
      'font-size:13px;font-weight:600;box-shadow:0 4px 12px rgba(0,0,0,.15);';
    el.innerHTML =
      '<span id="rp-offline-text">Hors ligne</span>' +
      ' <button type="button" id="rp-offline-retry" style="margin-left:10px;background:#f97316;border:0;color:#fff;font-weight:700;padding:6px 12px;border-radius:8px;font-size:12px;cursor:pointer;">Réessayer</button>';
    document.body.appendChild(el);
    document.getElementById('rp-offline-retry').addEventListener('click', function () {
      if (isOnline()) {
        flushQueue().then(function () {
          location.reload();
        });
      } else {
        location.reload();
      }
    });
    return el;
  }

  function updateBanner() {
    var el = ensureBanner();
    var q = getQueue();
    var text = document.getElementById('rp-offline-text');
    if (!isOnline()) {
      el.style.display = 'block';
      if (text) {
        text.textContent =
          q.length > 0
            ? 'Hors ligne — ' + q.length + ' action(s) en attente'
            : 'Hors ligne — certaines pages restent accessibles';
      }
      document.body.style.paddingTop = el.offsetHeight + 'px';
    } else {
      el.style.display = q.length ? 'block' : 'none';
      if (q.length && text) {
        text.textContent = q.length + ' action(s) en attente de synchro…';
      }
      document.body.style.paddingTop = el.style.display === 'block' ? el.offsetHeight + 'px' : '';
    }
  }

  /**
   * fetch avec repli hors-ligne pour les POST livreur (statut).
   * Utilisation : offlineFetch(url, { method:'POST', body:{statut:'LIVREE'} })
   */
  window.offlineFetch = async function (url, options) {
    options = options || {};
    if (isOnline()) {
      try {
        var headers = Object.assign(
          { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' },
          options.headers || {}
        );
        var res = await fetch(url, {
          method: options.method || 'POST',
          headers: headers,
          body: typeof options.body === 'string' ? options.body : JSON.stringify(options.body || {}),
        });
        return res;
      } catch (e) {
        // tombe en file d'attente
      }
    }
    window.queueOfflineAction({
      url: url,
      method: options.method || 'POST',
      body: options.body,
      headers: options.headers,
      label: options.label || url,
    });
    return {
      ok: true,
      offline: true,
      json: async function () {
        return { success: true, offline: true, message: 'Enregistré hors ligne' };
      },
    };
  };

  window.addEventListener('online', function () {
    updateBanner();
    flushQueue();
  });
  window.addEventListener('offline', function () {
    updateBanner();
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      updateBanner();
      if (isOnline()) flushQueue();
    });
  } else {
    updateBanner();
    if (isOnline()) flushQueue();
  }
})();
