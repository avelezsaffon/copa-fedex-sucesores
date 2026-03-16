// Chat widget para reglas de golf - Copa Fedex Sucesores 2026
(function() {
    var toggle = document.getElementById('chat-toggle');
    var panel = document.getElementById('chat-panel');
    var closeBtn = document.getElementById('chat-close');
    var form = document.getElementById('chat-form');
    var input = document.getElementById('chat-input');
    var messages = document.getElementById('chat-messages');

    // Historial de conversacion para contexto
    var historial = [];

    var navChat = document.getElementById('nav-chat');
    var clearBtn = document.getElementById('chat-clear');
    var copyBtn = document.getElementById('chat-copy');
    var welcomeMsg = 'Soy el Comisario de la Copa Fedex Sucesores 2026. Consulteme sobre cualquier situacion de reglas en el campo y le doy el veredicto con la regla oficial. Use los botones rapidos o escriba su pregunta.';

    // Botones de respuesta rapida
    var quickButtons = [
        { label: 'Bola perdida', text: 'Mi bola se perdio, no la encuentro. ¿Que hago?' },
        { label: 'Bola en agua', text: 'Mi bola cayo en un area de penalidad (agua). ¿Cuales son mis opciones?' },
        { label: 'Asiento mejorado', text: '¿Hoy aplica asiento mejorado? ¿Como funciona?' },
        { label: 'Bola injugable', text: 'Mi bola quedo en una posicion injugable. ¿Que opciones tengo?' },
        { label: 'Hoyo en uno', text: 'Alguien hizo hoyo en uno. ¿Cuanto se paga y como funciona?' },
        { label: 'Drop correcto', text: '¿Como se hace un drop correctamente?' }
    ];

    function addQuickButtons() {
        var container = document.createElement('div');
        container.className = 'chat-quick-buttons';
        quickButtons.forEach(function(btn) {
            var button = document.createElement('button');
            button.className = 'chat-quick-btn';
            button.textContent = btn.label;
            button.addEventListener('click', function() {
                sendMessage(btn.text);
                // Remover botones despues de usar uno
                var existing = messages.querySelector('.chat-quick-buttons');
                if (existing) existing.remove();
            });
            container.appendChild(button);
        });
        messages.appendChild(container);
        messages.scrollTop = messages.scrollHeight;
    }

    function openChat() {
        panel.classList.remove('hidden');
        input.focus();
    }

    toggle.addEventListener('click', function() {
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            input.focus();
        }
    });

    if (navChat) {
        navChat.addEventListener('click', function(e) {
            e.preventDefault();
            openChat();
        });
    }

    closeBtn.addEventListener('click', function() {
        panel.classList.add('hidden');
    });

    copyBtn.addEventListener('click', function() {
        var text = '';
        var msgs = messages.querySelectorAll('.chat-msg');
        msgs.forEach(function(msg) {
            if (msg.classList.contains('chat-typing')) return;
            if (msg.classList.contains('chat-user')) {
                text += 'Jugador: ' + msg.textContent + '\n\n';
            } else if (msg.classList.contains('chat-bot')) {
                text += 'Comisario: ' + msg.textContent + '\n\n';
            }
        });
        if (!text.trim()) return;
        text = '--- El Comisario - Copa Fedex Sucesores 2026 ---\n\n' + text;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                copyBtn.title = 'Copiado!';
                copyBtn.style.color = '#4caf50';
                setTimeout(function() {
                    copyBtn.title = 'Copiar conversacion';
                    copyBtn.style.color = '';
                }, 2000);
            });
        } else {
            var ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            copyBtn.title = 'Copiado!';
            setTimeout(function() { copyBtn.title = 'Copiar conversacion'; }, 2000);
        }
    });

    clearBtn.addEventListener('click', function() {
        historial = [];
        messages.innerHTML = '';
        var div = document.createElement('div');
        div.className = 'chat-msg chat-bot';
        div.textContent = welcomeMsg;
        messages.appendChild(div);
        addQuickButtons();
    });

    function addMessage(text, role) {
        // Remover botones rapidos si existen
        var existing = messages.querySelector('.chat-quick-buttons');
        if (existing) existing.remove();

        var div = document.createElement('div');
        div.className = 'chat-msg ' + (role === 'user' ? 'chat-user' : 'chat-bot');
        div.textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function addTypingIndicator() {
        var div = document.createElement('div');
        div.className = 'chat-msg chat-bot chat-typing';
        div.id = 'chat-typing';
        div.innerHTML = '<span class="dot-pulse"></span>';
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function removeTypingIndicator() {
        var el = document.getElementById('chat-typing');
        if (el) el.remove();
    }

    function sendMessage(text) {
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        input.disabled = true;

        historial.push({ role: 'user', content: text });

        addTypingIndicator();

        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensajes: historial })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            removeTypingIndicator();
            if (data.error) {
                addMessage('Error: ' + data.error, 'bot');
            } else {
                addMessage(data.respuesta, 'bot');
                historial.push({ role: 'assistant', content: data.respuesta });
            }
            input.disabled = false;
            input.focus();
        })
        .catch(function(err) {
            removeTypingIndicator();
            addMessage('Error de conexion. Intente de nuevo.', 'bot');
            input.disabled = false;
            input.focus();
        });
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage(input.value.trim());
    });

    // Mostrar botones rapidos al inicio
    addQuickButtons();
})();
