"""
Mateus AI - Рабочая версия с исправленными кнопками
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
        .chat-input-area {
            display: flex; gap: 10px; padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }
        #messageInput {
            flex: 1; padding: 15px; background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color); border-radius: 10px;
            color: var(--text-light); font-size: 1rem;
        }
        #sendButton {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: #0d3b0d; border: none; padding: 0 25px;
            border-radius: 10px; cursor: pointer; font-weight: bold;
            min-width: 100px;
        }
        .typing-indicator {
            display: none; padding: 15px; color: var(--text-muted);
            font-style: italic;
        }
        .footer {
            text-align: center; padding: 20px; color: var(--text-muted);
            border-top: 1px solid var(--border-color); margin-top: 20px;
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
                    <strong>Текущая роль:</strong> Помощник
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

                <div class="chat-messages" id="chatMessages">
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

        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            // Назначаем обработчики кнопкам ролей
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const role = this.getAttribute('data-role');
                    selectRole(role);
                });
            });
            
            // Обработчики других кнопок
            document.getElementById('applyCustomRole').addEventListener('click', applyCustomRole);
            document.getElementById('clearChat').addEventListener('click', clearChat);
            document.getElementById('sendButton').addEventListener('click', sendMessage);
            document.getElementById('messageInput').addEventListener('keypress', handleKeyPress);
            
            // Выбираем роль по умолчанию
            selectRole('assistant');
        });

        function selectRole(role) {
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
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    role_type: roleType,
                    role_description: roleDescription
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage('system', `Роль изменена на: ${roleDisplayNames[roleType] || 'Своя'}`);
                }
            });
        }

        function addMessage(sender, text) {
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
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            document.getElementById('typingIndicator').style.display = 'block';
            document.getElementById('sendButton').disabled = true;
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                
                if (data.success) {
                    addMessage('ai', data.response);
                } else {
                    addMessage('ai', 'Ошибка');
                }
            });
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function clearChat() {
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
                fetch('/clear_chat', {method: 'POST'});
            }
        }
    </script>
</body>
</html>
'''

DEFAULT_ROLES = {
    "assistant": "Вы - полезный AI-ассистент. Отвечайте на вопросы.",
    "psychologist": "Вы - психолог. Помогайте с эмоциональными вопросами.",
    "teacher": "Вы - учитель. Объясняйте темы просто и понятно.",
    "programmer": "Вы - программист. Помогайте с написанием кода."
}

session_roles = {}
session_histories = {}

@app.route('/')
def index():
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        session_roles[session_id] = DEFAULT_ROLES['assistant']
        session_histories[session_id] = []
    
    current_time = datetime.now().strftime("%H:%M")
    return render_template_string(HTML_TEMPLATE, current_time=current_time)

@app.route('/set_role', methods=['POST'])
def set_role():
    data = request.json
    session_id = session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False})
    
    role_type = data.get('role_type', 'assistant')
    role_description = data.get('role_description', '')
    
    if role_type in DEFAULT_ROLES:
        session_roles[session_id] = DEFAULT_ROLES[role_type]
    else:
        session_roles[session_id] = role_description
    
    return jsonify({'success': True})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False})
    
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'success': False})
    
    current_role = session_roles.get(session_id, DEFAULT_ROLES['assistant'])
    
    try:
        messages = [
            {"role": "system", "content": current_role},
            {"role": "user", "content": user_message}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        response_text = response.choices[0].message.content
        
        return jsonify({'success': True, 'response': response_text})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': True, 'response': 'Ответ от AI'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session_id = session.get('session_id')
    if session_id in session_histories:
        session_histories[session_id] = []
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    print(f"Starting Mateus AI on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
