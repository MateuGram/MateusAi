<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MateusAI – Чат с ИИ</title>
    <!-- Подключаем highlight.js (тёмная тема) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <!-- Подключаем marked.js для парсинга Markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        .chat-header h1 { font-size: 24px; margin-bottom: 5px; }
        .badge {
            display: inline-block;
            background: #ff9800;
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 12px;
            margin-left: 10px;
            vertical-align: middle;
        }
        .reset-btn {
            position: absolute;
            right: 20px;
            top: 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
        }
        .reset-btn:hover { background: rgba(255,255,255,0.3); }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 20px;
            display: flex;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message { justify-content: flex-end; }
        .bot-message { justify-content: flex-start; }
        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 20px;
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .user-message .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        .bot-message .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        /* Стили для блоков кода */
        .bot-message .message-content pre {
            position: relative;
            background: #282c34;
            border-radius: 8px;
            padding: 12px;
            margin: 12px 0;
            overflow-x: auto;
        }
        .bot-message .message-content pre code {
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #abb2bf;
            background: transparent;
            padding: 0;
            white-space: pre;
        }
        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #21252b;
            padding: 6px 12px;
            border-radius: 8px 8px 0 0;
            margin-top: 12px;
            font-size: 12px;
            color: #9da5b4;
        }
        .code-lang {
            font-weight: bold;
            text-transform: lowercase;
        }
        .copy-btn {
            background: #3e4451;
            border: none;
            color: #abb2bf;
            padding: 2px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            transition: background 0.2s;
        }
        .copy-btn:hover {
            background: #528bff;
            color: white;
        }
        .bot-message .message-content p code {
            background: #eee;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }
        .bot-message .message-content a {
            color: #667eea;
            text-decoration: none;
        }
        .bot-message .message-content a:hover {
            text-decoration: underline;
        }
        .message-time {
            font-size: 10px;
            margin-top: 5px;
            opacity: 0.6;
            text-align: right;
        }
        .typing-indicator {
            display: flex;
            padding: 12px 18px;
            background: white;
            border-radius: 20px;
            width: fit-content;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        .chat-input input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #eee;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input input:focus { border-color: #667eea; }
        .chat-input button {
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .chat-input button:hover { transform: translateY(-2px); }
        .chat-input button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>MateusAI <span class="badge">От MateuKras/span></h1>
            <p>Чат с нужным помощником</p>
            <button class="reset-btn" onclick="resetChat()">Очистить историю</button>
        </div>
        <div class="chat-messages" id="messages">
            <div class="message bot-message">
                <div class="message-content">
                    👋 Привет! Я MateusAI. Я поддерживаю <strong>жирный</strong>, <em>курсив</em>, <code>код</code>.
                    <div class="message-time">только что</div>
                </div>
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()" id="sendBtn">Отправить</button>
        </div>
    </div>

    <script>
        let isWaiting = false;

        // Функция для рендеринга Markdown с обработкой блоков кода
        function renderMarkdown(text) {
            if (!text) return '';
            const renderer = new marked.Renderer();
            renderer.code = function(code, language) {
                const lang = (language || 'plaintext').toLowerCase();
                const highlighted = hljs.highlight(code, { language: lang }).value;
                return `
                    <div class="code-header">
                        <span class="code-lang">${lang}</span>
                        <button class="copy-btn" onclick="copyCode(this)">Копировать</button>
                    </div>
                    <pre><code class="hljs ${lang}">${highlighted}</code></pre>
                `;
            };
            marked.setOptions({ renderer });
            return marked.parse(text);
        }

        // Функция копирования кода
        window.copyCode = function(btn) {
            const pre = btn.closest('pre');
            const code = pre.querySelector('code');
            const text = code.textContent;
            navigator.clipboard.writeText(text).then(() => {
                btn.textContent = 'Скопировано!';
                setTimeout(() => btn.textContent = 'Копировать', 2000);
            }).catch(() => alert('Не удалось скопировать'));
        };

        function addMessage(text, isUser) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            if (isUser) {
                messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}<div class="message-time">${time}</div></div>`;
            } else {
                messageDiv.innerHTML = `<div class="message-content">${renderMarkdown(text)}<div class="message-time">${time}</div></div>`;
            }
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            return messageDiv;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message || isWaiting) return;

            // Добавляем сообщение пользователя
            addMessage(message, true);
            input.value = '';

            // Создаём временное сообщение бота, которое будем обновлять
            const messagesDiv = document.getElementById('messages');
            const tempDiv = document.createElement('div');
            tempDiv.className = 'message bot-message';
            tempDiv.id = 'temp-message';
            const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            tempDiv.innerHTML = `<div class="message-content"><span class="typing-indicator"><span></span><span></span><span></span></span><div class="message-time">${time}</div></div>`;
            messagesDiv.appendChild(tempDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            isWaiting = true;
            document.getElementById('sendBtn').disabled = true;

            try {
                const response = await fetch('/chat-stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });

                    // Разбираем SSE-сообщения
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // последний кусок может быть неполным

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') continue;
                            try {
                                const obj = JSON.parse(data);
                                if (obj.type === 'token') {
                                    fullText += obj.content;
                                    // Обновляем сообщение бота с рендерингом Markdown
                                    tempDiv.innerHTML = `<div class="message-content">${renderMarkdown(fullText)}<div class="message-time">${time}</div></div>`;
                                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                                } else if (obj.type === 'error') {
                                    fullText = obj.content;
                                    tempDiv.innerHTML = `<div class="message-content">${escapeHtml(fullText)}<div class="message-time">${time}</div></div>`;
                                }
                            } catch (e) {
                                console.warn('Ошибка парсинга SSE:', e);
                            }
                        }
                    }
                }

                // Убираем временный ID
                tempDiv.removeAttribute('id');
                if (!fullText) {
                    tempDiv.innerHTML = `<div class="message-content">❌ Не удалось получить ответ<div class="message-time">${time}</div></div>`;
                }
            } catch (error) {
                console.error(error);
                tempDiv.innerHTML = `<div class="message-content">❌ Ошибка соединения. Попробуй ещё раз.<div class="message-time">${time}</div></div>`;
            } finally {
                isWaiting = false;
                document.getElementById('sendBtn').disabled = false;
            }
        }

        async function resetChat() {
            if (!confirm('Очистить всю историю диалога?')) return;
            try {
                await fetch('/reset', { method: 'POST' });
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = `
                    <div class="message bot-message">
                        <div class="message-content">
                            👋 История очищена. Начинаем новый диалог!
                            <div class="message-time">только что</div>
                        </div>
                    </div>
                `;
            } catch (error) {
                alert('Не удалось очистить историю');
            }
        }
    </script>
</body>
</html>
