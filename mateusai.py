"""
Mateus AI - Исправленная версия с работающим API
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session
import openai

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-secret-key-2024')

# Ваш API ключ
openai.api_key = "GCm6eM9QprwRlpNdmok3mi0r40lAacfg"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary-green: #1a5d1a; --secondary-green: #2e8b57;
            --light-green: #90ee90; --accent-green: #32cd32;
            --background: #0f1a0f; --card-bg: #1a2a1a;
            --text-light: #e8f5e8; --text-muted: #a3d9a3;
            --border-color: #2a5c2a;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--background) 0%, #0c2b0c 100%);
            color: var(--text-light); min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center; padding: 30px 20px;
            background: linear-gradient(135deg, var(--primary-green) 0%, #0d3b0d 100%);
            border-radius: 20px; margin-bottom: 30px;
            border: 2px solid var(--accent-green);
        }
        .logo {
            font-size: 3.5rem; margin-bottom: 10px;
            color: var(--light-green);
        }
        .title {
            font-size: 2.8rem; margin-bottom: 10px;
            background: linear-gradient(45deg, var(--light-green), var(--accent-green));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .subtitle {
            font-size: 1.2rem; color: var(--text-muted);
            margin-bottom: 20px;
        }
        .main-content {
            display: grid; grid-template-columns: 1fr 2fr;
            gap: 25px; margin-bottom: 30px;
        }
        @media (max-width: 900px) {
            .main-content { grid-template-columns: 1fr; }
        }
        .role-panel {
            background: var(--card-bg); border-radius: 15px;
            padding: 25px; border: 1px solid var(--border-color);
        }
        .role-title {
            font-size: 1.5rem; margin-bottom: 20px;
            color: var(--light-green);
            display: flex; align-items: center; gap: 10px;
        }
        .role-presets {
            display: grid; grid-template-columns: 1fr;
            gap: 12px; margin-bottom: 25px;
        }
        .role-btn {
            background: linear-gradient(135deg, var(--primary-green), var(--secondary-green));
            border: none; color: white; padding: 14px; border-radius: 10px;
            cursor: pointer; font-size: 1rem; transition: all 0.3s ease;
            text-align: left; display: flex; align-items: center; gap: 10px;
            border: 1px solid transparent;
        }
        .role-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(46, 139, 87, 0.4);
            border-color: var(--accent-green);
        }
        .role-btn.active {
            background: linear-gradient(135deg, var(--secondary-green), var(--accent-green));
            border-color: var(--light-green);
        }
        .custom-role { margin-top: 20px; }
        .custom-role textarea {
            width: 100%; min-height: 150px; background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color); border-radius: 10px;
            padding: 15px; color: var(--text-light); font-size: 1rem;
            resize: vertical; margin-bottom: 15px;
        }
        .apply-btn {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: #0d3b0d; border: none; padding: 12px 25px;
            border-radius: 10px; cursor: pointer; font-weight: bold;
            width: 100%; display: flex; justify-content: center;
            align-items: center; gap: 10px;
        }
        .chat-panel {
            background: var(--card-bg); border-radius: 15px;
            padding: 25px; border: 1px solid var(--border-color);
            display: flex; flex-direction: column; height: 600px;
        }
        .chat-header {
            margin-bottom: 20px; padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            display: flex; align-items: center; justify-content: space-between;
        }
        .chat-header h3 {
            font-size: 1.5rem; color: var(--light-green);
            display: flex; align-items: center; gap: 10px;
        }
        .clear-chat-btn {
            background: rgba(139, 0, 0, 0.2);
            color: #ff6b6b; border: 1px solid #ff6b6b;
            padding: 8px 15px; border-radius: 8px;
            cursor: pointer; font-size: 0.9rem;
            transition: all 0.3s ease;
            display: flex; align-items: center; gap: 8px;
        }
        .clear-chat-btn:hover {
            background: rgba(139, 0, 0, 0.4);
        }
        .chat-messages {
            flex: 1; overflow-y: auto; margin-bottom: 20px;
            padding-right: 10px;
        }
        .message {
            margin-bottom: 20px; padding: 15px; border-radius: 15px;
            max-width: 80%; animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message {
            background: linear-gradient(135deg, var(--primary-green), var(--secondary-green));
            margin-left: auto; border-bottom-right-radius: 5px;
        }
        .ai-message {
            background: rgba(46, 139, 87, 0.2);
            border: 1px solid var(--border-color);
            margin-right: auto; border-bottom-left-radius: 5px;
        }
        .message-header {
            display: flex; align-items: center;
            gap: 10px; margin-bottom: 8px; font-weight: bold;
        }
        .message-content {
            line-height: 1.5;
        }
        .message-time {
            font-size: 0.8rem; color: var(--text-muted);
            text-align: right; margin-top: 5px;
        }
        .chat-input-area {
            display: flex; gap: 10px; padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }
        #messageInput {
            flex: 1; padding: 15px; background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color); border-radius: 10px;
            color: var(--text-light); font-size: 1rem;
        }
        #messageInput:focus {
            outline: none; border-color: var(--accent-green);
        }
        #sendButton {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: #0d3b0d; border: none; padding: 0 25px;
            border-radius: 10px; cursor: pointer; font-weight: bold;
            display: flex; align-items: center; gap: 8px;
            min-width: 100px; justify-content: center;
        }
        #sendButton:hover {
            transform: translateY(-2px);
        }
        #sendButton:disabled {
            opacity: 0.6; cursor: not-allowed; transform: none;
        }
        .typing-indicator {
            display: none; padding: 15px; color: var(--text-muted);
            font-style: italic; align-items: center; gap: 10px;
        }
        .typing-dots {
            display: flex; gap: 5px;
        }
        .typing-dots span {
            width: 8px; height: 8px; background: var(--accent-green);
            border-radius: 50%; animation: typing 1.4s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .footer {
            text-align: center; padding: 20px; color: var(--text-muted);
            border-top: 1px solid var(--border-color); margin-top: 20px;
        }
        .role-description {
            margin-top: 15px; padding: 15px;
            background: rgba(0, 0, 0, 0.2); border-radius: 10px;
            border-left: 4px solid var(--accent-green);
            font-size: 0.9rem; color: var(--text-muted);
        }
        .scrollbar::-webkit-scrollbar { width: 8px; }
        .scrollbar::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2); border-radius: 4px;
        }
        .scrollbar::-webkit-scrollbar-thumb {
            background: var(--secondary-green); border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo"><i class="fas fa-brain"></i>Mateus AI</div>
            <h1 class="title">Интеллектуальный помощник</h1>
            <p class="subtitle">Полная версия с OpenAI GPT-3.5</p>
        </div>

        <div class="main-content">
            <div class="role-panel">
                <h3 class="role-title"><i class="fas fa-mask"></i>Выбор роли</h3>
                
                <div class="role-presets">
                    <button class="role-btn" data-role="assistant">
                        <i class="fas fa-robot"></i>Помощник
                    </button>
                    <button class="role-btn" data-role="psychologist">
                        <i class="fas fa-heart"></i>Психолог
                    </button>
                    <button class="role-btn" data-role="teacher">
                        <i class="fas fa-graduation-cap"></i>Учитель
                    </button>
                    <button class="role-btn" data-role="programmer">
                        <i class="fas fa-code"></i>Программист
                    </button>
                </div>

                <div class="role-description" id="roleDescription">
                    <strong>Текущая роль:</strong> Помощник<br>
                    Вы - полезный AI-ассистент. Помогайте с вопросами.
                </div>

                <div class="custom-role">
                    <h4><i class="fas fa-edit"></i> Своя роль:</h4>
                    <textarea id="customRoleText" placeholder="Опишите роль..."></textarea>
                    <button class="apply-btn" id="applyCustomRole">
                        <i class="fas fa-check"></i> Применить
                    </button>
                </div>
            </div>

            <div class="chat-panel">
                <div class="chat-header">
                    <h3><i class="fas fa-comments"></i> Чат</h3>
                    <button class="clear-chat-btn" id="clearChat">
                        <i class="fas fa-trash"></i> Очистить
                    </button>
                </div>

                <div class="chat-messages scrollbar" id="chatMessages">
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-robot"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            Здравствуйте! Я Mateus AI. Выберите роль и начните общение.
                        </div>
                        <div class="message-time">{{ current_time }}</div>
                    </div>
                </div>

                <div class="typing-indicator" id="typingIndicator">
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                    Mateus AI печатает...
                </div>

                <div class="chat-input-area">
                    <input type="text" id="messageInput" placeholder="Введите сообщение...">
                    <button id="sendButton">
                        <i class="fas fa-paper-plane"></i> Отправить
                    </button>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Mateus AI | Порты: 3498/5000</p>
        </div>
    </div>

    <script>
        // ДЕБАГ: Проверяем загрузку скрипта
        console.log('Mateus AI script loaded');
        
        let currentRole = 'assistant';
        let conversationHistory = [];
        
        const roleDescriptions = {
            'assistant': 'Вы - полезный AI-ассистент. Помогайте с вопросами.',
            'psychologist': 'Вы - психолог. Помогайте с эмоциональными вопросами.',
            'teacher': 'Вы - учитель. Объясняйте темы просто.',
            'programmer': 'Вы - программист. Помогайте с кодом.'
        };

        const roleDisplayNames = {
            'assistant': 'Помощник',
            'psychologist': 'Психолог',
            'teacher': 'Учитель',
            'programmer': 'Программист',
            'custom': 'Своя роль'
        };

        // Функция выбора роли
        function selectRole(role) {
            console.log('Selecting role:', role);
            currentRole = role;
            
            // Обновление кнопок
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-role') === role) {
                    btn.classList.add('active');
                }
            });
            
            // Обновление описания
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> ${roleDisplayNames[role]}<br>
                ${roleDescriptions[role]}
            `;
            
            // Отправка на сервер
            applyRole(role, roleDescriptions[role]);
        }

        function applyCustomRole() {
            console.log('Applying custom role');
            const customRoleText = document.getElementById('customRoleText').value.trim();
            if (!customRoleText) {
                alert('Опишите роль');
                return;
            }
            
            currentRole = 'custom';
            
            // Обновление кнопок
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Обновление описания
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> Своя роль<br>
                ${customRoleText.substring(0, 100)}...
            `;
            
            // Отправка на сервер
            applyRole('custom', customRoleText);
        }

        function applyRole(roleType, roleDescription) {
            console.log('Applying role to server:', roleType);
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    role_type: roleType,
                    role_description: roleDescription
                })
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Server response:', data);
                if (data.success) {
                    addMessage('system', `Роль изменена на: ${roleDisplayNames[roleType] || 'Своя'}`);
                } else {
                    console.error('Failed to set role:', data.error);
                }
            })
            .catch(error => {
                console.error('Error applying role:', error);
            });
        }

        function addMessage(sender, text) {
            console.log('Adding message:', sender, text.substring(0, 50));
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            if (sender === 'user') {
                messageDiv.className = 'message user-message';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-user"></i> Вы
                    </div>
                    <div class="message-content">${text}</div>
                    <div class="message-time">${timestamp}</div>
                `;
            } else if (sender === 'ai') {
                messageDiv.className = 'message ai-message';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-robot"></i> Mateus AI
                    </div>
                    <div class="message-content">${text}</div>
                    <div class="message-time">${timestamp}</div>
                `;
            } else if (sender === 'system') {
                messageDiv.className = 'message ai-message';
                messageDiv.style.backgroundColor = 'rgba(70, 130, 180, 0.2)';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-info-circle"></i> Система
                    </div>
                    <div class="message-content"><em>${text}</em></div>
                    <div class="message-time">${timestamp}</div>
                `;
            }
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function sendMessage() {
            console.log('Sending message');
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) {
                console.log('Empty message, skipping');
                return;
            }
            
            addMessage('user', message);
            input.value = '';
            
            document.getElementById('typingIndicator').style.display = 'flex';
            document.getElementById('sendButton').disabled = true;
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => {
                console.log('Chat response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Chat response data:', data);
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                
                if (data.success) {
                    addMessage('ai', data.response);
                } else {
                    addMessage('ai', 'Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Error sending message:', error);
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                addMessage('ai', 'Ошибка соединения с сервером');
            });
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendMessage();
            }
        }

        function clearChat() {
            console.log('Clearing chat');
            if (confirm('Очистить чат?')) {
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-robot"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            Чат очищен.
                        </div>
                        <div class="message-time">${new Date().toLocaleTimeString()}</div>
                    </div>
                `;
                fetch('/clear_chat', {method: 'POST'})
                .then(response => response.json())
                .then(data => console.log('Clear chat response:', data));
            }
        }

        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing...');
            
            // Назначаем обработчики кнопкам ролей
            document.querySelectorAll('.role-btn').forEach(btn => {
                console.log('Adding listener to role button:', btn.getAttribute('data-role'));
                btn.addEventListener('click', function() {
                    const role = this.getAttribute('data-role');
                    console.log('Role button clicked:', role);
                    selectRole(role);
                });
            });
            
            // Обработчики других кнопок
            document.getElementById('applyCustomRole').addEventListener('click', applyCustomRole);
            document.getElementById('clearChat').addEventListener('click', clearChat);
            document.getElementById('sendButton').addEventListener('click', sendMessage);
            document.getElementById('messageInput').addEventListener('keypress', handleKeyPress);
            
            // Выбираем роль по умолчанию
            console.log('Selecting default role...');
            selectRole('assistant');
            
            // Проверяем связь с сервером
            fetch('/health')
                .then(response => response.json())
                .then(data => console.log('Health check:', data))
                .catch(error => console.error('Health check failed:', error));
            
            console.log('Initialization complete');
        });
    </script>
</body>
</html>
'''

# Улучшенные роли
DEFAULT_ROLES = {
    "assistant": "Вы - полезный AI-ассистент Mateus AI. Отвечайте на вопросы ясно и подробно. Будьте дружелюбны и полезны.",
    "psychologist": "Вы - психолог Mateus AI. Выслушивайте проблемы пользователя, давайте советы по ментальному здоровью и эмоциональному благополучию. Будьте эмпатичны.",
    "teacher": "Вы - учитель Mateus AI. Объясняйте сложные темы простыми словами. Помогайте с обучением и образованием.",
    "programmer": "Вы - программист Mateus AI. Помогайте с написанием кода, отладкой и техническими вопросами. Давайте практичные советы."
}

# Хранилище сессий
session_roles = {}
session_histories = {}

@app.route('/')
def index():
    """Главная страница"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            session_roles[session_id] = DEFAULT_ROLES['assistant']
            session_histories[session_id] = []
        
        current_time = datetime.now().strftime("%H:%M")
        return render_template_string(HTML_TEMPLATE, current_time=current_time)
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"Error: {e}", 500

@app.route('/set_role', methods=['POST'])
def set_role():
    """Установка роли"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'})
        
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        role_type = data.get('role_type', 'assistant')
        role_description = data.get('role_description', '')
        
        print(f"Setting role for session {session_id}: {role_type}")
        
        if role_type in DEFAULT_ROLES:
            session_roles[session_id] = DEFAULT_ROLES[role_type]
        else:
            session_roles[session_id] = role_description
        
        return jsonify({'success': True, 'role': role_type})
    except Exception as e:
        print(f"Error in set_role: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    """Обработка сообщений"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data'})
        
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({'success': False, 'error': 'Empty message'})
        
        print(f"Chat request from session {session_id}: {user_message[:50]}...")
        
        # Получаем роль
        current_role = session_roles.get(session_id, DEFAULT_ROLES['assistant'])
        
        # Проверяем API ключ
        if not openai.api_key or openai.api_key == "GCm6eM9QprwRlpNdmok3mi0r40lAacfg":
            # Используем реальный API
            try:
                messages = [
                    {"role": "system", "content": current_role},
                    {"role": "user", "content": user_message}
                ]
                
                print("Calling OpenAI API...")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                
                response_text = response.choices[0].message.content
                print(f"OpenAI response: {response_text[:50]}...")
                
                # Сохраняем в историю
                if session_id not in session_histories:
                    session_histories[session_id] = []
                
                session_histories[session_id].append({
                    'sender': 'user',
                    'text': user_message,
                    'time': datetime.now().isoformat()
                })
                session_histories[session_id].append({
                    'sender': 'ai',
                    'text': response_text,
                    'time': datetime.now().isoformat()
                })
                
                return jsonify({'success': True, 'response': response_text})
                
            except openai.error.AuthenticationError as e:
                print(f"OpenAI Authentication Error: {e}")
                return jsonify({
                    'success': False, 
                    'error': 'Ошибка аутентификации OpenAI API. Проверьте API ключ.',
                    'response': 'Проверьте API ключ в настройках.'
                })
            except openai.error.RateLimitError as e:
                print(f"OpenAI Rate Limit Error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Лимит запросов OpenAI. Попробуйте позже.',
                    'response': 'Лимит запросов. Попробуйте через минуту.'
                })
            except Exception as e:
                print(f"OpenAI Error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'response': f'Ошибка OpenAI: {str(e)[:100]}'
                })
        else:
            # Демо режим (если ключ не установлен)
            responses = {
                'assistant': f'Как помощник, я могу сказать: "{user_message}" - это хороший вопрос!',
                'psychologist': 'Как психолог, я рекомендую обсудить это с близкими или специалистом.',
                'teacher': 'Как учитель, я бы объяснил эту тему с примерами и практикой.',
                'programmer': 'Как программист, я бы посоветовал изучить документацию и писать чистый код.'
            }
            
            response_text = responses.get('assistant', 'Спасибо за вопрос!')
            return jsonify({'success': True, 'response': response_text})
            
    except Exception as e:
        print(f"Error in chat route: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Очистка истории"""
    try:
        session_id = session.get('session_id')
        if session_id in session_histories:
            session_histories[session_id] = []
            print(f"Chat cleared for session {session_id}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in clear_chat: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Проверка здоровья"""
    try:
        # Проверяем API ключ
        api_status = "active" if openai.api_key else "inactive"
        
        return jsonify({
            'status': 'healthy',
            'service': 'Mateus AI',
            'openai_api': api_status,
            'sessions': len(session_roles),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/debug')
def debug():
    """Страница отладки"""
    return jsonify({
        'session_id': session.get('session_id'),
        'session_roles': list(session_roles.keys()),
        'session_histories': {k: len(v) for k, v in session_histories.items()},
        'openai_api_key_set': bool(openai.api_key)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    
    print("=" * 60)
    print("🤖 MATEUS AI - ЗАПУСК СЕРВЕРА")
    print("=" * 60)
    print(f"🔑 API ключ: {'✅ УСТАНОВЛЕН' if openai.api_key else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"🌐 Порт: {port}")
    print(f"🚀 Запуск на: http://localhost:{port}")
    print("=" * 60)
    
    # Тестируем API ключ
    if openai.api_key:
        try:
            print("Проверка API ключа...")
            models = openai.Model.list(limit=1)
            print(f"✅ API ключ работает! Доступно моделей: {len(models.data) if models.data else 0}")
        except openai.error.AuthenticationError:
            print("❌ ОШИБКА АУТЕНТИФИКАЦИИ API!")
            print("Проверьте API ключ. Возможно он неверный или истек.")
        except Exception as e:
            print(f"⚠️  Ошибка при проверке API: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
