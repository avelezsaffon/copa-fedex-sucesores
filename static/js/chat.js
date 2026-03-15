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
    var welcomeMsg = 'Que hubo pues parcero! Soy el hijueputa experto en reglas de golf de la Copa Fedex Sucesores. Pregunteme una situacion y le digo si hay penalidad, cuantos golpes y por cual regla. No me salga con maricadas que no sean de golf.';

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

    clearBtn.addEventListener('click', function() {
        historial = [];
        messages.innerHTML = '';
        var div = document.createElement('div');
        div.className = 'chat-msg chat-bot';
        div.textContent = welcomeMsg;
        messages.appendChild(div);
    });

    function addMessage(text, role) {
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

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        var text = input.value.trim();
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
            addMessage('Error de conexion. Intenta de nuevo.', 'bot');
            input.disabled = false;
            input.focus();
        });
    });
})();
