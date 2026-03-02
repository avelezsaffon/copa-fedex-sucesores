var _adminAuth = null;

function getAdminAuth() {
    if (_adminAuth) return _adminAuth;
    var pwd = prompt('Clave de administrador:');
    if (!pwd) return null;
    _adminAuth = 'Basic ' + btoa('admin:' + pwd);
    return _adminAuth;
}

function adminFetch(url, options) {
    var auth = getAdminAuth();
    if (!auth) return Promise.reject(new Error('Sin clave'));
    options = options || {};
    options.headers = options.headers || {};
    options.headers['Authorization'] = auth;
    return fetch(url, options).then(function(r) {
        if (r.status === 401) {
            _adminAuth = null;
            throw new Error('Clave incorrecta');
        }
        return r;
    });
}

function showNotification(message, type) {
    var el = document.getElementById('notification');
    if (!el) return;
    el.textContent = message;
    el.className = 'notification ' + type;
    if (type !== 'loading') {
        setTimeout(function() { el.className = 'notification hidden'; }, 4000);
    }
}

async function toggleRonda(rondaId, checkbox) {
    try {
        var response = await fetch('/api/ronda/' + rondaId + '/toggle', { method: 'POST' });
        var data = await response.json();
        checkbox.checked = data.aplicable;
        var row = checkbox.closest('tr');
        if (data.aplicable) {
            row.classList.add('row-aplicable');
        } else {
            row.classList.remove('row-aplicable');
        }
        showNotification(
            data.aplicable ? 'Ronda marcada como aplicable' : 'Ronda desmarcada',
            'success'
        );
    } catch (e) {
        showNotification('Error al cambiar estado', 'error');
        checkbox.checked = !checkbox.checked;
    }
}

async function syncJugador(jugadorId, btn) {
    btn.disabled = true;
    var originalText = btn.textContent;
    btn.textContent = 'Sincronizando...';
    showNotification('Sincronizando rondas...', 'loading');
    try {
        var response = await fetch('/api/sync/jugador/' + jugadorId, { method: 'POST' });
        var data = await response.json();
        showNotification(data.nuevas_rondas + ' rondas nuevas encontradas', 'success');
        if (data.nuevas_rondas > 0) {
            setTimeout(function() { location.reload(); }, 1500);
        } else {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    } catch (e) {
        showNotification('Error al sincronizar', 'error');
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

async function syncAll() {
    showNotification('Sincronizando todos los jugadores... esto puede tomar un momento', 'loading');
    try {
        var response = await fetch('/api/sync/all', { method: 'POST' });
        var data = await response.json();
        showNotification(
            data.jugadores_sincronizados + ' jugadores sincronizados, ' +
            data.rondas_nuevas + ' rondas nuevas',
            'success'
        );
        if (data.rondas_nuevas > 0) {
            setTimeout(function() { location.reload(); }, 2000);
        }
    } catch (e) {
        showNotification('Error al sincronizar', 'error');
    }
}

async function recalcular() {
    showNotification('Recalculando ranking...', 'loading');
    try {
        var response = await adminFetch('/api/recalcular', { method: 'POST' });
        var data = await response.json();
        showNotification(
            'Ranking recalculado: ' + data.jugadores_en_ranking + ' jugadores',
            'success'
        );
        setTimeout(function() { location.reload(); }, 1500);
    } catch (e) {
        showNotification(e.message === 'Clave incorrecta' ? 'Clave incorrecta' : 'Error al recalcular', 'error');
    }
}
