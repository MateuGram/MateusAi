"""
Mateus AI - Искусственный интеллект с функциями ролевого поведения
Адаптировано для Render.com (порт 3498)
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session
import openai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
# Для Render используем переменные окружения
app.secret_key = os.getenv('SECRET_KEY', os.environ.get('SECRET_KEY', 'mateus-ai-secret-key-render-2024'))

# Настройка OpenAI - сначала проверяем переменные окружения Render, потом .env
openai.api_key = os.environ.get('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))

# HTML шаблон с зелёным дизайном
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI - Ваш интеллектуальный помощник</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-green: #1a5d1a;
            --secondary-green: #2e8b57;
            --light-green: #90ee90;
            --dark-green: #0d3b0d;
            --accent-green: #32cd32;
            --background: #0f1a0f;
            --card-bg: #1a2a1a;
            --text-light: #e8f5e8;
            --text-muted: #a3d9a3;
            --border-color: #2a5c2a;
            --render-blue: #46b3b8;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--background) 0%, #0c2b0c 100%);
            color: var(--text-light);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            padding: 30px 20px;
            background: linear-gradient(135deg, var(--primary-green) 0%, var(--dark-green) 100%);
            border-radius: 20px;
            margin-bottom: 30px;
            border: 2px solid var(--accent-green);
            box-shadow: 0 10px 30px rgba(26, 93, 26, 0.3);
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, transparent 30%, rgba(144, 238, 144, 0.1) 70%);
            animation: pulse 15s infinite linear;
        }

        @keyframes pulse {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .logo {
            font-size: 3.5rem;
            margin-bottom: 10px;
            color: var(--light-green);
            text-shadow: 0 0 20px var(--accent-green);
            position: relative;
            z-index: 1;
        }

        .logo i {
            margin-right: 15px;
        }

        .title {
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, var(--light-green), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
            z-index: 1;
        }

        .subtitle {
            font-size: 1.2rem;
            color: var(--text-muted);
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }

        .render-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--render-blue);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            text-decoration: none;
            margin-top: 10px;
            font-size: 0.9rem;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 25px;
            margin-bottom: 30px;
        }

        @media (max-width: 900px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }

        .role-panel {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid var(--border-color);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .role-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: var(--light-green);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .role-title i {
            color: var(--accent-green);
        }

        .role-presets {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            margin-bottom: 25px;
        }

        .role-btn {
            background: linear-gradient(135deg, var(--primary-green), var(--secondary-green));
            border: none;
            color: white;
            padding: 14px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            text-align: left;
            display: flex;
            align-items: center;
            gap: 10px;
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

        .custom-role {
            margin-top: 20px;
        }

        .custom-role textarea {
            width: 100%;
            min-height: 150px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 15px;
            color: var(--text-light);
            font-size: 1rem;
            resize: vertical;
            margin-bottom: 15px;
            transition: border-color 0.3s ease;
        }

        .custom-role textarea:focus {
            outline: none;
            border-color: var(--accent-green);
            box-shadow: 0 0 10px rgba(50, 205, 50, 0.3);
        }

        .apply-btn {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: var(--dark-green);
            border: none;
            padding: 12px 25px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }

        .apply-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(144, 238, 144, 0.4);
        }

        .chat-panel {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid var(--border-color);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            height: 600px;
        }

        .chat-header {
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chat-header h3 {
            font-size: 1.5rem;
            color: var(--light-green);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .clear-chat-btn {
            background: rgba(139, 0, 0, 0.2);
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
            padding: 8px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .clear-chat-btn:hover {
            background: rgba(139, 0, 0, 0.4);
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding-right: 10px;
        }

        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 15px;
            max-width: 80%;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            background: linear-gradient(135deg, var(--primary-green), var(--secondary-green));
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }

        .ai-message {
            background: rgba(46, 139, 87, 0.2);
            border: 1px solid var(--border-color);
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }

        .message-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
            font-weight: bold;
        }

        .message-content {
            line-height: 1.5;
        }

        .message-time {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-align: right;
            margin-top: 5px;
        }

        .chat-input-area {
            display: flex;
            gap: 10px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
        }

        #messageInput {
            flex: 1;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-light);
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }

        #messageInput:focus {
            outline: none;
            border-color: var(--accent-green);
            box-shadow: 0 0 10px rgba(50, 205, 50, 0.3);
        }

        #sendButton {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: var(--dark-green);
            border: none;
            padding: 0 25px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 100px;
            justify-content: center;
        }

        #sendButton:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(144, 238, 144, 0.4);
        }

        #sendButton:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .typing-indicator {
            display: none;
            padding: 15px;
            color: var(--text-muted);
            font-style: italic;
            align-items: center;
            gap: 10px;
        }

        .typing-dots {
            display: flex;
            gap: 5px;
        }

        .typing-dots span {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: var(--text-muted);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 20px;
        }

        .role-description {
            margin-top: 15px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            border-left: 4px solid var(--accent-green);
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        .scrollbar::-webkit-scrollbar {
            width: 8px;
        }

        .scrollbar::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }

        .scrollbar::-webkit-scrollbar-thumb {
            background: var(--secondary-green);
            border-radius: 4px;
        }

        .scrollbar::-webkit-scrollbar-thumb:hover {
            background: var(--accent-green);
        }

        .server-info {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .info-item {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            background: rgba(70, 179, 184, 0.1);
            border-radius: 10px;
            border: 1px solid var(--render-blue);
        }

        @media (max-width: 768px) {
            .header {
                padding: 20px 15px;
            }
            
            .logo {
                font-size: 2.5rem;
            }
            
            .title {
                font-size: 2rem;
            }
            
            .chat-panel {
                height: 500px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <i class="fas fa-brain"></i>Mateus AI
            </div>
            <h1 class="title">Интеллектуальный помощник с ролевым поведением</h1>
            <p class="subtitle">Выберите роль или создайте свою - AI адаптируется под ваши нужды</p>
            
            <a href="https://render.com" target="_blank" class="render-badge">
                <i class="fas fa-cloud"></i> Развернуто на Render | Порт: 3498
            </a>
            
            <div class="server-info">
                <div class="info-item">
                    <i class="fas fa-plug"></i> Статус: <span id="serverStatus">🟢 Активен</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-bolt"></i> Режим: <span id="aiMode">{{ mode }}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-user"></i> Сессия: <span id="sessionId">...</span>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="role-panel">
                <h3 class="role-title"><i class="fas fa-mask"></i>Выбор роли</h3>
                
                <div class="role-presets">
                    <button class="role-btn" onclick="selectRole('assistant')">
                        <i class="fas fa-robot"></i>Помощник
                    </button>
                    <button class="role-btn" onclick="selectRole('psychologist')">
                        <i class="fas fa-heart"></i>Психолог
                    </button>
                    <button class="role-btn" onclick="selectRole('teacher')">
                        <i class="fas fa-graduation-cap"></i>Учитель
                    </button>
                    <button class="role-btn" onclick="selectRole('programmer')">
                        <i class="fas fa-code"></i>Программист
                    </button>
                    <button class="role-btn" onclick="selectRole('friend')">
                        <i class="fas fa-user-friends"></i>Друг
                    </button>
                    <button class="role-btn" onclick="selectRole('creative')">
                        <i class="fas fa-palette"></i>Креативщик
                    </button>
                </div>

                <div class="role-description" id="roleDescription">
                    <strong>Текущая роль:</strong> Помощник<br>
                    Вы - Mateus AI, полезный и дружелюбный AI-ассистент.
                </div>

                <div class="custom-role">
                    <h4><i class="fas fa-edit"></i> Своя роль:</h4>
                    <textarea id="customRoleText" placeholder="Опишите роль для Mateus AI... Например: 'Вы - опытный шеф-повар, который дает советы по приготовлению блюд...'"></textarea>
                    <button class="apply-btn" onclick="applyCustomRole()">
                        <i class="fas fa-check"></i> Применить роль
                    </button>
                </div>
            </div>

            <div class="chat-panel">
                <div class="chat-header">
                    <h3><i class="fas fa-comments"></i> Чат с Mateus AI</h3>
                    <button class="clear-chat-btn" onclick="clearChat()">
                        <i class="fas fa-trash"></i> Очистить чат
                    </button>
                </div>

                <div class="chat-messages scrollbar" id="chatMessages">
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-robot"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            Здравствуйте! Я Mateus AI - ваш интеллектуальный помощник, развернутый на Render.com. Выберите мою роль слева или создайте свою собственную!
                        </div>
                        <div class="message-time">{{ current_time }}</div>
                    </div>
                </div>

                <div class="typing-indicator" id="typingIndicator">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    Mateus AI печатает...
                </div>

                <div class="chat-input-area">
                    <input type="text" id="messageInput" placeholder="Введите ваше сообщение..." onkeypress="handleKeyPress(event)">
                    <button id="sendButton" onclick="sendMessage()">
                        <i class="fas fa-paper-plane"></i> Отправить
                    </button>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Mateus AI. Все права защищены. | Развернуто на Render.com | Порт: 3498 | Система ролевого поведения AI</p>
            <p style="margin-top: 10px; font-size: 0.8rem;">
                <i class="fas fa-info-circle"></i> 
                {% if api_available %}
                Режим: Полный (OpenAI API доступен)
                {% else %}
                Режим: Демонстрационный (для работы с OpenAI API установите OPENAI_API_KEY)
                {% endif %}
            </p>
        </div>
    </div>

    <script>
        let currentRole = 'assistant';
        let conversationHistory = [];
        let sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
        
        // Отображаем ID сессии
        document.getElementById('sessionId').textContent = sessionId.substr(0, 8) + '...';
        
        const roleDescriptions = {
            'assistant': 'Вы - Mateus AI, полезный и дружелюбный AI-ассистент. Вы помогаете пользователям с различными задачами, отвечаете на вопросы и поддерживаете беседу.',
            'psychologist': 'Вы - психолог Mateus AI. Вы помогаете пользователям с их эмоциональными проблемами, слушаете внимательно и даете профессиональные советы по улучшению психического здоровья.',
            'teacher': 'Вы - учитель Mateus AI. Вы объясняете сложные темы простыми словами, помогаете с обучением и образованием. Вы терпеливы и хорошо объясняете.',
            'programmer': 'Вы - программист Mateus AI. Вы помогаете с написанием кода, отладкой, архитектурой программ и техническими вопросами. Даете четкие и практичные советы.',
            'friend': 'Вы - друг Mateus AI. Вы общаетесь как близкий друг, поддерживаете неформальные беседы, шутите и создаете комфортную атмосферу.',
            'creative': 'Вы - креативный помощник Mateus AI. Вы помогаете с генерацией идей, творческими проектами, написанием текстов и художественных произведений.'
        };

        const roleDisplayNames = {
            'assistant': 'Помощник',
            'psychologist': 'Психолог',
            'teacher': 'Учитель',
            'programmer': 'Программист',
            'friend': 'Друг',
            'creative': 'Креативщик',
            'custom': 'Пользовательская роль'
        };

        function selectRole(role) {
            currentRole = role;
            
            // Обновление кнопок
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
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
                alert('Пожалуйста, опишите роль для AI');
                return;
            }
            
            currentRole = 'custom';
            
            // Обновление кнопок
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Обновление описания
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> Пользовательская роль<br>
                ${customRoleText}
            `;
            
            // Отправка на сервер
            applyRole('custom', customRoleText);
        }

        function applyRole(roleType, roleDescription) {
            fetch('/set_role', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    role_type: roleType,
                    role_description: roleDescription,
                    session_id: sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage('system', `Роль изменена на: ${roleDisplayNames[roleType] || 'Пользовательская'}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
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
            
            // Сохраняем в историю
            if (sender === 'user' || sender === 'ai') {
                conversationHistory.push({
                    sender: sender,
                    text: text,
                    time: timestamp
                });
            }
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Добавляем сообщение пользователя
            addMessage('user', message);
            input.value = '';
            
            // Показываем индикатор набора
            document.getElementById('typingIndicator').style.display = 'flex';
            document.getElementById('sendButton').disabled = true;
            
            // Отправляем на сервер
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(-10),
                    session_id: sessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Скрываем индикатор набора
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                
                if (data.success) {
                    addMessage('ai', data.response);
                } else {
                    addMessage('ai', 'Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                addMessage('ai', 'Ошибка соединения с сервером Render. Проверьте подключение к интернету.');
            });
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function clearChat() {
            if (confirm('Очистить всю историю чата?')) {
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-robot"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            Чат очищен. Чем я могу вам помочь?
                        </div>
                        <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                    </div>
                `;
                conversationHistory = [];
                
                // Очищаем историю на сервере
                fetch('/clear_chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ session_id: sessionId })
                });
            }
        }

        // Инициализация - выбираем помощника по умолчанию
        document.addEventListener('DOMContentLoaded', function() {
            selectRole('assistant');
            
            // Проверка связи с сервером
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'healthy') {
                        document.getElementById('serverStatus').innerHTML = '🟢 Активен';
                    }
                })
                .catch(() => {
                    document.getElementById('serverStatus').innerHTML = '⚠️ Проверка...';
                });
        });
    </script>
</body>
</html>
'''

# Роли по умолчанию
DEFAULT_ROLES = {
    "assistant": "Вы - Mateus AI, полезный и дружелюбный AI-ассистент. Вы помогаете пользователям с различными задачами, отвечаете на вопросы и поддерживаете беседу.",
    "psychologist": "Вы - психолог Mateus AI. Вы помогаете пользователям с их эмоциональными проблемами, слушаете внимательно и даете профессиональные советы по улучшению психического здоровья.",
    "teacher": "Вы - учитель Mateus AI. Вы объясняете сложные темы простыми словами, помогаете с обучением и образованием. Вы терпеливы и хорошо объясняете.",
    "programmer": "Вы - программист Mateus AI. Вы помогаете с написанием кода, отладкой, архитектурой программ и техническими вопросами. Даете четкие и практичные советы.",
    "friend": "Вы - друг Mateus AI. Вы общаетесь как близкий друг, поддерживаете неформальные беседы, шутите и создаете комфортную атмосферу.",
    "creative": "Вы - креативный помощник Mateus AI. Вы помогаете с генерацией идей, творческими проектами, написанием текстов и художественных произведений."
}

# Хранилище для сессий (в памяти, для демо)
session_roles = {}
session_histories = {}

@app.route('/')
def index():
    """Главная страница"""
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        session_roles[session_id] = DEFAULT_ROLES['assistant']
        session_histories[session_id] = []
    
    current_time = datetime.now().strftime("%H:%M")
    
    # Проверяем наличие API ключа
    api_available = bool(openai.api_key)
    mode = "Полный (с OpenAI API)" if api_available else "Демонстрационный"
    
    return render_template_string(HTML_TEMPLATE, 
                                 current_time=current_time, 
                                 mode=mode,
                                 api_available=api_available)

@app.route('/set_role', methods=['POST'])
def set_role():
    """Установка роли для AI"""
    data = request.json
    session_id = data.get('session_id') or session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Сессия не найдена'})
    
    role_type = data.get('role_type', 'assistant')
    role_description = data.get('role_description', '')
    
    if role_type in DEFAULT_ROLES:
        session_roles[session_id] = DEFAULT_ROLES[role_type]
    else:
        session_roles[session_id] = role_description
    
    # Очищаем историю при смене роли
    if session_id in session_histories:
        session_histories[session_id] = []
    
    return jsonify({'success': True, 'role': role_type})

@app.route('/chat', methods=['POST'])
def chat():
    """Обработка сообщений пользователя"""
    data = request.json
    session_id = data.get('session_id') or session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Сессия не найдена'})
    
    user_message = data.get('message', '')
    history = data.get('history', [])
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Пустое сообщение'})
    
    # Получаем текущую роль
    current_role = session_roles.get(session_id, DEFAULT_ROLES['assistant'])
    
    try:
        # Проверяем, есть ли API ключ
        if not openai.api_key:
            # ДЕМОНСТРАЦИОННЫЙ РЕЖИМ - умные ответы на основе роли
            if "психолог" in current_role.lower():
                responses = [
                    "Как психолог, я рекомендую вам уделить время саморефлексии. Что именно вызывает у вас эти чувства?",
                    "Важно признавать свои эмоции. Попробуйте описать, что вы чувствуете, более подробно.",
                    "Психологическое благополучие начинается с самопонимания. Давайте обсудим это глубже."
                ]
            elif "учитель" in current_role.lower():
                responses = [
                    "Отличный вопрос для обучения! Давайте разберем эту тему по шагам...",
                    "Как учитель, я объясню это простыми словами. Начнем с основ...",
                    "Для лучшего понимания, давайте рассмотрим практический пример..."
                ]
            elif "программист" in current_role.lower():
                responses = [
                    "В программировании важно понимать логику. Какая именно часть кода вас интересует?",
                    "Давайте разберем эту техническую проблему. Какие ошибки вы видите?",
                    "Для решения этой задачи можно использовать несколько подходов..."
                ]
            elif "друг" in current_role.lower():
                responses = [
                    "Привет! Как твои дела? Расскажи мне больше о том, что происходит.",
                    "Все бывает, друг. Главное - не сдаваться! Что думаешь делать дальше?",
                    "Я здесь, чтобы поддержать тебя. Давай обсудим это как друзья!"
                ]
            elif "креатив" in current_role.lower():
                responses = [
                    "Отличная идея для творческого проекта! Что если мы добавим...",
                    "Креативный подход требует вдохновения. Давайте поищем нестандартные решения!",
                    "Для вашего творческого проекта рекомендую рассмотреть несколько вариантов..."
                ]
            else:
                # Общие ответы помощника
                responses = [
                    "Я помогу вам с этим вопросом. Можете рассказать подробнее?",
                    "Интересный вопрос! Давайте рассмотрим его с разных сторон.",
                    "Чтобы дать точный ответ, мне нужно немного больше информации.",
                    "Спасибо за вопрос! Я постараюсь помочь вам наилучшим образом.",
                    "Давайте обсудим это. Что именно вас интересует?"
                ]
            
            import random
            response = random.choice(responses)
            
        else:
            # РЕЖИМ С OPENAI API
            messages_history = []
            
            # Добавляем системное сообщение с ролью
            messages_history.append({"role": "system", "content": current_role})
            
            # Добавляем историю из сессии
            if session_id in session_histories:
                for msg in session_histories[session_id][-10:]:
                    if msg['sender'] == 'user':
                        messages_history.append({"role": "user", "content": msg['text']})
                    else:
                        messages_history.append({"role": "assistant", "content": msg['text']})
            
            # Добавляем текущее сообщение
            messages_history.append({"role": "user", "content": user_message})
            
            # Запрос к OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages_history,
                temperature=0.7,
                max_tokens=500
            )
            response = response.choices[0].message.content
        
        # Сохраняем в историю сессии
        if session_id not in session_histories:
            session_histories[session_id] = []
        
        session_histories[session_id].append({
            'sender': 'user',
            'text': user_message,
            'time': datetime.now().isoformat()
        })
        session_histories[session_id].append({
            'sender': 'ai',
            'text': response,
            'time': datetime.now().isoformat()
        })
        
        return jsonify({'success': True, 'response': response})
    
    except Exception as e:
        print(f"Error: {e}")
        # Возвращаем дружелюбный ответ даже при ошибке
        error_responses = [
            "Извините, возникли временные технические трудности. Пожалуйста, попробуйте еще раз.",
            "Произошла ошибка при обработке запроса. Давайте попробуем снова?",
            "К сожалению, сервер временно не отвечает. Пожалуйста, повторите попытку."
        ]
        import random
        return jsonify({
            'success': True, 
            'response': random.choice(error_responses)
        })

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Очистка истории чата"""
    data = request.json
    session_id = data.get('session_id') if data else session.get('session_id')
    
    if session_id and session_id in session_histories:
        session_histories[session_id] = []
    
    return jsonify({'success': True})

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья сервера (нужен для Render)"""
    return jsonify({
        'status': 'healthy',
        'service': 'Mateus AI',
        'port': 3498,
        'timestamp': datetime.now().isoformat(),
        'sessions': len(session_roles),
        'mode': 'full' if openai.api_key else 'demo'
    })

@app.route('/render-info')
def render_info():
    """Информация о развертывании на Render"""
    return jsonify({
        'deployed_on': 'Render.com',
        'port': 3498,
        'api_available': bool(openai.api_key),
        'version': '1.0.0'
    })

# Основная функция запуска
if __name__ == '__main__':
    # Получаем порт из переменной окружения Render, или используем 3498
    port = int(os.environ.get('PORT', 3498))
    
    print("=" * 60)
    print("🤖 MATEUS AI - ИНТЕЛЛЕКТУАЛЬНЫЙ ПОМОЩНИК")
    print("=" * 60)
    print(f"🌐 РАЗВЕРНУТО НА RENDER.COM")
    print(f"🔌 ПОРТ: {port}")
    print("=" * 60)
    
    if not openai.api_key:
        print("⚠️  РЕЖИМ: ДЕМОНСТРАЦИОННЫЙ")
        print("ℹ️  Для использования OpenAI API:")
        print("ℹ️  1. Получите ключ на https://platform.openai.com/api-keys")
        print("ℹ️  2. Добавьте OPENAI_API_KEY в Environment Variables на Render")
        print("ℹ️  3. Или установите в файле .env для локальной разработки")
    else:
        print("✅ РЕЖИМ: ПОЛНЫЙ (OpenAI API доступен)")
        print("✅ Все функции активны")
    
    print("=" * 60)
    print(f"🚀 СЕРВЕР ЗАПУСКАЕТСЯ...")
    print(f"🔗 ОТКРОЙТЕ: http://localhost:{port}")
    print("=" * 60)
    
    # Запускаем сервер
    app.run(debug=False, host='0.0.0.0', port=port)
