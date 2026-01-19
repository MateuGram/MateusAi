"""
Mateus AI - Нейросеть с админ-панелью и PRO подпиской
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import openai
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-secret-key-2024')

# ВАШ API КЛЮЧ
openai.api_key = "sk-40b9bc396e3a492393618f7f725c6278"

# Настройки
MAX_CONTEXT_LENGTH = 8000
MAX_HISTORY_MESSAGES = 20

# Пароль админ-панели
ADMIN_PASSWORD = "Qwerty123Admin123"

# База данных пользователей (в памяти для демо)
users_db = {
    # 'user_id': {'requests_today': 0, 'last_request_date': '2024-01-01', 'is_pro': False, 'pro_until': None}
}

# Админ пользователи
admin_users = {
    'admin': {'password': ADMIN_PASSWORD, 'is_admin': True}
}

# Лимиты
FREE_LIMIT = 10
PRO_LIMIT = 1000

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI 🤖</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary-green: #1a5d1a; --secondary-green: #2e8b57;
            --light-green: #90ee90; --accent-green: #32cd32;
            --background: #0f1a0f; --card-bg: #1a2a1a;
            --text-light: #e8f5e8; --text-muted: #a3d9a3;
            --border-color: #2a5c2a; --gold: #ffd700;
            --blue: #1e90ff; --purple: #9370db; --red: #ff6b6b;
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
            position: relative; overflow: hidden;
        }
        .header::before {
            content: ''; position: absolute; top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, transparent 30%, rgba(144, 238, 144, 0.1) 70%);
            animation: pulse 15s infinite linear;
        }
        @keyframes pulse {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .logo {
            font-size: 3.5rem; margin-bottom: 10px;
            color: var(--light-green); text-shadow: 0 0 20px var(--accent-green);
            position: relative; z-index: 1;
        }
        .title {
            font-size: 2.8rem; margin-bottom: 10px;
            background: linear-gradient(45deg, var(--light-green), var(--accent-green), var(--gold));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            position: relative; z-index: 1;
        }
        .subtitle {
            font-size: 1.2rem; color: var(--text-muted);
            margin-bottom: 20px; position: relative; z-index: 1;
        }
        .api-status {
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(50, 205, 50, 0.2); padding: 8px 15px;
            border-radius: 20px; border: 1px solid var(--accent-green);
            margin-top: 10px; font-size: 0.9rem; position: relative; z-index: 1;
        }
        .status-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #32cd32; animation: pulse 2s infinite;
        }
        .limits-info {
            display: flex; justify-content: center; gap: 20px;
            margin-top: 15px; flex-wrap: wrap; position: relative; z-index: 1;
        }
        .limit-item {
            display: flex; align-items: center; gap: 8px;
            padding: 8px 15px; border-radius: 15px;
            font-size: 0.9rem;
        }
        .free-limit {
            background: rgba(147, 112, 219, 0.2);
            border: 1px solid var(--purple);
        }
        .pro-limit {
            background: rgba(255, 215, 0, 0.2);
            border: 1px solid var(--gold);
        }
        .request-count {
            background: rgba(30, 144, 255, 0.2);
            border: 1px solid var(--blue);
        }
        .admin-link {
            position: absolute; top: 20px; right: 20px;
            background: rgba(255, 107, 107, 0.2);
            color: var(--red); padding: 8px 15px;
            border-radius: 10px; text-decoration: none;
            border: 1px solid var(--red);
            font-size: 0.9rem; z-index: 2;
            transition: all 0.3s ease;
        }
        .admin-link:hover {
            background: rgba(255, 107, 107, 0.4);
            transform: translateY(-2px);
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
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .role-title {
            font-size: 1.5rem; margin-bottom: 20px;
            color: var(--light-green); display: flex; align-items: center; gap: 10px;
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
            border-color: var(--light-green); box-shadow: 0 0 15px rgba(50, 205, 50, 0.5);
        }
        .custom-role { margin-top: 20px; }
        .custom-role textarea {
            width: 100%; min-height: 150px; background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color); border-radius: 10px;
            padding: 15px; color: var(--text-light); font-size: 1rem;
            resize: vertical; margin-bottom: 15px; transition: all 0.3s ease;
        }
        .custom-role textarea:focus {
            outline: none; border-color: var(--accent-green);
            box-shadow: 0 0 15px rgba(50, 205, 50, 0.3);
        }
        .apply-btn {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: #0d3b0d; border: none; padding: 12px 25px;
            border-radius: 10px; cursor: pointer; font-weight: bold;
            font-size: 1rem; transition: all 0.3s ease; width: 100%;
            display: flex; justify-content: center; align-items: center; gap: 10px;
        }
        .apply-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(144, 238, 144, 0.4);
        }
        .chat-panel {
            background: var(--card-bg); border-radius: 15px;
            padding: 25px; border: 1px solid var(--border-color);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
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
            background: rgba(139, 0, 0, 0.2); color: #ff6b6b;
            border: 1px solid #ff6b6b; padding: 8px 15px;
            border-radius: 8px; cursor: pointer; font-size: 0.9rem;
            transition: all 0.3s ease; display: flex; align-items: center; gap: 8px;
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
        .message-content strong { color: var(--accent-green); }
        .message-content em { color: var(--text-muted); }
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
            color: var(--text-light); font-size: 1rem; transition: all 0.3s ease;
        }
        #messageInput:focus {
            outline: none; border-color: var(--accent-green);
            box-shadow: 0 0 15px rgba(50, 205, 50, 0.3);
        }
        #sendButton {
            background: linear-gradient(135deg, var(--accent-green), var(--light-green));
            color: #0d3b0d; border: none; padding: 0 25px;
            border-radius: 10px; cursor: pointer; font-weight: bold;
            font-size: 1rem; transition: all 0.3s ease; display: flex;
            align-items: center; gap: 8px; min-width: 100px; justify-content: center;
        }
        #sendButton:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(144, 238, 144, 0.4);
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
        .scrollbar::-webkit-scrollbar-thumb:hover {
            background: var(--accent-green);
        }
        .ai-intelligence {
            display: flex; justify-content: center; gap: 20px;
            margin-top: 15px; flex-wrap: wrap; position: relative; z-index: 1;
        }
        .intel-item {
            display: flex; align-items: center; gap: 5px;
            padding: 5px 10px; background: rgba(70, 179, 184, 0.1);
            border-radius: 10px; border: 1px solid #46b3b8;
        }
        .thinking {
            font-style: italic; color: var(--accent-green);
            padding: 5px; font-size: 0.9rem;
        }
        .pro-badge {
            background: linear-gradient(45deg, #ffd700, #ffaa00);
            color: #333; padding: 3px 10px;
            border-radius: 12px; font-weight: bold;
            font-size: 0.8rem; margin-left: 10px;
        }
        .limit-warning {
            background: rgba(255, 107, 107, 0.2);
            border: 1px solid var(--red); padding: 10px;
            border-radius: 10px; margin-top: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/admin" class="admin-link">
                <i class="fas fa-cog"></i> Админ-панель
            </a>
            
            <div class="logo"><i class="fas fa-brain"></i>Mateus AI</div>
            <h1 class="title">Умная нейросеть с PRO подпиской</h1>
            <p class="subtitle">Бесплатно: {{ free_limit }} запросов | PRO: {{ pro_limit }} запросов в день</p>
            
            <div class="api-status">
                <span class="status-dot"></span>
                🤖 OpenAI API: 🟢 АКТИВЕН
            </div>
            
            <div class="limits-info">
                <div class="limit-item request-count">
                    <i class="fas fa-chart-line"></i>
                    <span id="requestsUsed">{{ requests_used }}</span>/<span id="requestsLimit">{{ requests_limit }}</span> запросов сегодня
                </div>
                <div class="limit-item free-limit">
                    <i class="fas fa-user"></i> Бесплатно: {{ free_limit }}
                </div>
                <div class="limit-item pro-limit">
                    <i class="fas fa-crown"></i> PRO: {{ pro_limit }}
                </div>
            </div>
            
            <div id="limitWarning" style="display: none;" class="limit-warning">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Лимит запросов исчерпан!</strong>
                <span id="upgradeMessage"></span>
            </div>
        </div>

        <div class="main-content">
            <div class="role-panel">
                <h3 class="role-title"><i class="fas fa-mask"></i>Экспертные роли</h3>
                
                <div class="role-presets">
                    <button class="role-btn" data-role="assistant">
                        <i class="fas fa-robot"></i>Супер-помощник
                    </button>
                    <button class="role-btn" data-role="psychologist">
                        <i class="fas fa-brain"></i>Психолог-гений
                    </button>
                    <button class="role-btn" data-role="teacher">
                        <i class="fas fa-graduation-cap"></i>Профессор
                    </button>
                    <button class="role-btn" data-role="programmer">
                        <i class="fas fa-code"></i>Гуру программирования
                    </button>
                </div>

                <div class="role-description" id="roleDescription">
                    <strong>Текущая роль:</strong> Супер-помощник<br>
                    Вы - Mateus AI с доступом к GPT-4. Отвечайте подробно и умно.
                </div>

                <div class="custom-role">
                    <h4><i class="fas fa-edit"></i> Создать свою роль:</h4>
                    <textarea id="customRoleText" placeholder="Опишите эксперта..."></textarea>
                    <button class="apply-btn" id="applyCustomRoleBtn">
                        <i class="fas fa-bolt"></i> Активировать
                    </button>
                </div>
            </div>

            <div class="chat-panel">
                <div class="chat-header">
                    <h3><i class="fas fa-comments"></i> Чат с Mateus AI</h3>
                    <button class="clear-chat-btn" id="clearChatBtn">
                        <i class="fas fa-trash"></i> Очистить
                    </button>
                </div>

                <div class="chat-messages scrollbar" id="chatMessages">
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-brain"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            <strong>🚀 Добро пожаловать!</strong><br><br>
                            У вас <strong><span id="remainingRequests">{{ remaining_requests }}</span></strong> запросов доступно сегодня.<br>
                            PRO пользователи получают до {{ pro_limit }} запросов в день!
                        </div>
                        <div class="message-time">{{ current_time }}</div>
                    </div>
                </div>

                <div class="typing-indicator" id="typingIndicator">
                    <div class="typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                    <span class="thinking">Думаю...</span>
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
            <p>© 2024 Mateus AI | Бесплатно: {{ free_limit }} запр. | PRO: {{ pro_limit }} запр.</p>
        </div>
    </div>

    <script>
        // Переменные
        let currentRole = 'assistant';
        let conversationHistory = [];
        let currentUser = null;
        
        // Лимиты с сервера
        const freeLimit = {{ free_limit }};
        const proLimit = {{ pro_limit }};
        const isProUser = {{ 'true' if is_pro else 'false' }};
        const requestsUsed = {{ requests_used }};
        const requestsLimit = {{ requests_limit }};
        
        // Описания ролей
        const roleDescriptions = {
            'assistant': `Ты - Mateus AI, умный помощник. Отвечай подробно и полезно.`,
            'psychologist': `Ты - профессиональный психолог. Помогай с эмоциональными вопросами.`,
            'teacher': `Ты - опытный учитель. Объясняй сложные темы просто.`,
            'programmer': `Ты - senior разработчик. Помогай с кодом и технологиями.`
        };

        const roleDisplayNames = {
            'assistant': 'Супер-помощник',
            'psychologist': 'Психолог-гений', 
            'teacher': 'Профессор',
            'programmer': 'Гуру программирования',
            'custom': 'Свой эксперт'
        };

        // Проверка лимита запросов
        function checkRequestLimit() {
            const remaining = requestsLimit - requestsUsed;
            document.getElementById('remainingRequests').textContent = remaining;
            
            if (remaining <= 0) {
                const warning = document.getElementById('limitWarning');
                const message = isProUser ? 
                    'Ваш PRO лимит исчерпан. Лимит обновится завтра.' :
                    'Бесплатный лимит исчерпан. Перейдите на PRO для большего количества запросов.';
                
                document.getElementById('upgradeMessage').textContent = message;
                warning.style.display = 'block';
                return false;
            }
            
            if (remaining <= 3 && !isProUser) {
                const warning = document.getElementById('limitWarning');
                warning.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Осталось ${remaining} запросов!</strong>
                    Перейдите на PRO для увеличения лимита до ${proLimit}.
                `;
                warning.style.display = 'block';
            }
            
            return true;
        }
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Mateus AI loaded');
            
            // Проверяем лимит
            checkRequestLimit();
            
            // Кнопки ролей
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const role = this.getAttribute('data-role');
                    selectRole(role);
                });
            });
            
            // Другие кнопки
            document.getElementById('applyCustomRoleBtn').addEventListener('click', applyCustomRole);
            document.getElementById('clearChatBtn').addEventListener('click', clearChat);
            document.getElementById('sendButton').addEventListener('click', sendMessage);
            document.getElementById('messageInput').addEventListener('keypress', handleKeyPress);
            
            // Выбираем роль по умолчанию
            selectRole('assistant');
            
            // Обновляем счетчик запросов
            updateRequestCounter();
        });
        
        // Выбор роли
        function selectRole(role) {
            console.log('Выбор роли:', role);
            currentRole = role;
            
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-role') === role) {
                    btn.classList.add('active');
                }
            });
            
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> ${roleDisplayNames[role]}<br>
                ${roleDescriptions[role]}
            `;
            
            applyRoleToServer(role, roleDescriptions[role]);
        }
        
        // Применение своей роли
        function applyCustomRole() {
            const customRoleText = document.getElementById('customRoleText').value.trim();
            if (!customRoleText) {
                alert('Опишите роль');
                return;
            }
            
            currentRole = 'custom';
            
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> Свой эксперт<br>
                ${customRoleText.substring(0, 100)}...
            `;
            
            applyRoleToServer('custom', customRoleText);
        }
        
        // Отправка роли на сервер
        function applyRoleToServer(roleType, roleDescription) {
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
                    addSystemMessage(`✅ Роль изменена на: ${roleDisplayNames[roleType] || 'Свой эксперт'}`);
                }
            })
            .catch(error => {
                console.error('Ошибка установки роли:', error);
            });
        }
        
        // Добавление сообщений
        function addMessage(sender, text, isSystem = false) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            if (isSystem) {
                messageDiv.className = 'message ai-message';
                messageDiv.style.backgroundColor = 'rgba(70, 130, 180, 0.3)';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-cog"></i> Система
                    </div>
                    <div class="message-content">${text}</div>
                    <div class="message-time">${timestamp}</div>
                `;
            } else if (sender === 'user') {
                messageDiv.className = 'message user-message';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-user"></i> Вы
                    </div>
                    <div class="message-content">${text}</div>
                    <div class="message-time">${timestamp}</div>
                `;
                conversationHistory.push({sender: 'user', text: text});
            } else if (sender === 'ai') {
                messageDiv.className = 'message ai-message';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-brain"></i> ${roleDisplayNames[currentRole] || 'Mateus AI'}
                    </div>
                    <div class="message-content">${formatResponse(text)}</div>
                    <div class="message-time">${timestamp}</div>
                `;
                conversationHistory.push({sender: 'ai', text: text});
            }
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function addSystemMessage(text) {
            addMessage('ai', text, true);
        }
        
        // Форматирование ответа
        function formatResponse(text) {
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .replace(/^/, '<p>')
                .replace(/$/, '</p>');
        }
        
        // Отправка сообщения
        function sendMessage() {
            // Проверяем лимит
            if (!checkRequestLimit()) {
                alert('Лимит запросов исчерпан!');
                return;
            }
            
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) {
                alert('Введите сообщение!');
                return;
            }
            
            addMessage('user', message);
            input.value = '';
            
            // Показываем индикатор
            document.getElementById('typingIndicator').style.display = 'flex';
            document.getElementById('sendButton').disabled = true;
            
            // Отправляем на сервер
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(-6)
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                
                if (data.success) {
                    addMessage('ai', data.response);
                    // Обновляем счетчик запросов
                    updateRequestCounter(data.requests_used, data.requests_limit);
                } else {
                    if (data.error === 'limit_exceeded') {
                        addSystemMessage('🚫 Лимит запросов исчерпан!');
                        checkRequestLimit();
                    } else {
                        addMessage('ai', `Ошибка: ${data.error || 'Неизвестная ошибка'}`);
                    }
                }
            })
            .catch(error => {
                console.error('Ошибка отправки:', error);
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                addMessage('ai', 'Ошибка соединения');
            });
        }
        
        // Обновление счетчика запросов
        function updateRequestCounter(used = null, limit = null) {
            if (used !== null && limit !== null) {
                document.getElementById('requestsUsed').textContent = used;
                document.getElementById('requestsLimit').textContent = limit;
                const remaining = limit - used;
                document.getElementById('remainingRequests').textContent = remaining;
                checkRequestLimit();
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function clearChat() {
            if (confirm('Очистить чат?')) {
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-brain"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            Чат очищен.
                        </div>
                        <div class="message-time">${new Date().toLocaleTimeString()}</div>
                    </div>
                `;
                conversationHistory = [];
                fetch('/clear_chat', {method: 'POST'});
            }
        }
    </script>
</body>
</html>
'''

# HTML для админ-панели
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель Mateus AI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f1a0f 0%, #0c2b0c 100%);
            color: #e8f5e8; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center; padding: 30px 20px;
            background: linear-gradient(135deg, #1a5d1a 0%, #0d3b0d 100%);
            border-radius: 20px; margin-bottom: 30px;
            border: 2px solid #32cd32;
        }
        .logo {
            font-size: 2.5rem; margin-bottom: 10px;
            color: #90ee90;
        }
        .admin-panel {
            background: #1a2a1a; border-radius: 15px;
            padding: 30px; border: 1px solid #2a5c2a;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .tabs {
            display: flex; gap: 10px; margin-bottom: 20px;
            border-bottom: 1px solid #2a5c2a; padding-bottom: 10px;
        }
        .tab {
            background: #2e8b57; color: white; border: none;
            padding: 10px 20px; border-radius: 8px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .tab.active {
            background: #32cd32; transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(50, 205, 50, 0.3);
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(0, 0, 0, 0.3); padding: 20px;
            border-radius: 10px; border: 1px solid #2a5c2a;
        }
        .stat-card h3 {
            color: #90ee90; margin-bottom: 10px;
            display: flex; align-items: center; gap: 10px;
        }
        .stat-number {
            font-size: 2rem; font-weight: bold;
            color: #32cd32; margin: 10px 0;
        }
        .users-list {
            max-height: 400px; overflow-y: auto;
            margin-top: 20px;
        }
        .user-item {
            background: rgba(0, 0, 0, 0.2); padding: 15px;
            border-radius: 10px; margin-bottom: 10px;
            border: 1px solid #2a5c2a;
            display: flex; justify-content: space-between;
            align-items: center;
        }
        .user-info { flex: 1; }
        .user-actions { display: flex; gap: 10px; }
        .btn {
            padding: 8px 15px; border-radius: 6px;
            border: none; cursor: pointer; font-weight: bold;
            transition: all 0.3s ease;
        }
        .btn-pro {
            background: linear-gradient(45deg, #ffd700, #ffaa00);
            color: #333;
        }
        .btn-free {
            background: #9370db; color: white;
        }
        .btn-delete {
            background: #ff6b6b; color: white;
        }
        .btn:hover { transform: translateY(-2px); }
        .search-box {
            width: 100%; padding: 12px; margin-bottom: 20px;
            background: rgba(0, 0, 0, 0.3); border: 1px solid #2a5c2a;
            border-radius: 8px; color: #e8f5e8; font-size: 1rem;
        }
        .search-box:focus {
            outline: none; border-color: #32cd32;
            box-shadow: 0 0 10px rgba(50, 205, 50, 0.3);
        }
        .login-form {
            max-width: 400px; margin: 50px auto;
            background: #1a2a1a; padding: 40px;
            border-radius: 15px; border: 1px solid #2a5c2a;
            text-align: center;
        }
        .login-form input {
            width: 100%; padding: 12px; margin: 10px 0;
            background: rgba(0, 0, 0, 0.3); border: 1px solid #2a5c2a;
            border-radius: 8px; color: #e8f5e8; font-size: 1rem;
        }
        .login-form button {
            width: 100%; padding: 12px; margin-top: 20px;
            background: linear-gradient(135deg, #32cd32, #90ee90);
            color: #0d3b0d; border: none; border-radius: 8px;
            font-weight: bold; cursor: pointer; font-size: 1rem;
        }
        .back-link {
            display: inline-block; margin-top: 20px;
            color: #90ee90; text-decoration: none;
        }
        .pro-badge {
            background: linear-gradient(45deg, #ffd700, #ffaa00);
            color: #333; padding: 3px 10px; border-radius: 12px;
            font-weight: bold; font-size: 0.8rem; margin-left: 10px;
        }
        .message {
            padding: 15px; margin: 10px 0; border-radius: 8px;
            text-align: center;
        }
        .success { background: rgba(50, 205, 50, 0.2); color: #90ee90; }
        .error { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
    </style>
</head>
<body>
    <div class="container">
        {% if not logged_in %}
        <div class="login-form">
            <div class="logo"><i class="fas fa-lock"></i> Админ-панель</div>
            <h2>Вход в админ-панель</h2>
            
            {% if error %}
            <div class="message error">
                <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            {% endif %}
            
            <form method="POST">
                <input type="text" name="username" placeholder="Логин" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">
                    <i class="fas fa-sign-in-alt"></i> Войти
                </button>
            </form>
            <a href="/" class="back-link">
                <i class="fas fa-arrow-left"></i> Вернуться на главную
            </a>
        </div>
        {% else %}
        <div class="header">
            <div class="logo"><i class="fas fa-cog"></i> Админ-панель Mateus AI</div>
            <h1>Управление системой</h1>
            <p>Всего пользователей: {{ total_users }} | PRO: {{ pro_users }} | Активных: {{ active_users }}</p>
            <a href="/" class="back-link">
                <i class="fas fa-arrow-left"></i> Вернуться на главную
            </a>
        </div>
        
        <div class="admin-panel">
            <div class="tabs">
                <button class="tab active" onclick="showTab('stats')">
                    <i class="fas fa-chart-bar"></i> Статистика
                </button>
                <button class="tab" onclick="showTab('users')">
                    <i class="fas fa-users"></i> Пользователи
                </button>
                <button class="tab" onclick="showTab('settings')">
                    <i class="fas fa-sliders-h"></i> Настройки
                </button>
            </div>
            
            {% if message %}
            <div class="message {{ 'success' if message_type == 'success' else 'error' }}">
                <i class="fas fa-{{ 'check-circle' if message_type == 'success' else 'exclamation-circle' }}"></i>
                {{ message }}
            </div>
            {% endif %}
            
            <div id="stats" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3><i class="fas fa-users"></i> Пользователи</h3>
                        <div class="stat-number">{{ total_users }}</div>
                        <p>Всего зарегистрировано</p>
                    </div>
                    <div class="stat-card">
                        <h3><i class="fas fa-crown"></i> PRO пользователи</h3>
                        <div class="stat-number">{{ pro_users }}</div>
                        <p>{{ (pro_users/total_users*100 if total_users > 0 else 0)|round(1) }}% от всех</p>
                    </div>
                    <div class="stat-card">
                        <h3><i class="fas fa-comments"></i> Запросы сегодня</h3>
                        <div class="stat-number">{{ today_requests }}</div>
                        <p>Всего выполнено сегодня</p>
                    </div>
                    <div class="stat-card">
                        <h3><i class="fas fa-server"></i> Система</h3>
                        <div class="stat-number">{{ '{:.1f}'.format(memory_usage) }} MB</div>
                        <p>Использовано памяти</p>
                    </div>
                </div>
                
                <h3><i class="fas fa-chart-line"></i> Активность по дням</h3>
                <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin-top: 10px;">
                    {% for day, count in daily_stats.items() %}
                    <div style="display: flex; align-items: center; margin: 5px 0;">
                        <span style="width: 100px;">{{ day }}</span>
                        <div style="flex: 1; height: 20px; background: #2a5c2a; border-radius: 10px;">
                            <div style="height: 100%; background: #32cd32; border-radius: 10px; width: {{ (count/max_requests*100 if max_requests > 0 else 0)|int }}%;"></div>
                        </div>
                        <span style="margin-left: 10px; width: 50px; text-align: right;">{{ count }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div id="users" class="tab-content">
                <input type="text" class="search-box" id="userSearch" placeholder="Поиск пользователей..." onkeyup="searchUsers()">
                
                <div class="users-list" id="usersList">
                    {% for user_id, user_data in users.items() %}
                    <div class="user-item">
                        <div class="user-info">
                            <strong>ID: {{ user_id[:8] }}...</strong>
                            <div style="font-size: 0.9rem; color: #a3d9a3; margin-top: 5px;">
                                Запросов сегодня: {{ user_data.requests_today }}/{{ user_data.limit }}
                                {% if user_data.is_pro %}<span class="pro-badge">PRO</span>{% endif %}
                            </div>
                            <div style="font-size: 0.8rem; color: #a3d9a3;">
                                Создан: {{ user_data.created_date }}
                                {% if user_data.is_pro and user_data.pro_until %}
                                | PRO до: {{ user_data.pro_until }}
                                {% endif %}
                            </div>
                        </div>
                        <div class="user-actions">
                            {% if not user_data.is_pro %}
                            <button class="btn btn-pro" onclick="togglePro('{{ user_id }}', true)">
                                <i class="fas fa-crown"></i> Сделать PRO
                            </button>
                            {% else %}
                            <button class="btn btn-free" onclick="togglePro('{{ user_id }}', false)">
                                <i class="fas fa-user"></i> Убрать PRO
                            </button>
                            {% endif %}
                            <button class="btn btn-delete" onclick="deleteUser('{{ user_id }}')">
                                <i class="fas fa-trash"></i> Удалить
                            </button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <div style="margin-top: 20px;">
                    <h3><i class="fas fa-user-plus"></i> Добавить пользователя</h3>
                    <form method="POST" action="/admin/add_user" style="display: flex; gap: 10px; margin-top: 10px;">
                        <input type="text" name="user_id" placeholder="ID пользователя" style="flex: 1;">
                        <select name="is_pro" style="padding: 12px; background: rgba(0,0,0,0.3); border: 1px solid #2a5c2a; color: #e8f5e8; border-radius: 8px;">
                            <option value="false">Бесплатный</option>
                            <option value="true">PRO</option>
                        </select>
                        <input type="number" name="limit" placeholder="Лимит" value="10" min="1" max="10000" style="width: 100px;">
                        <button type="submit" class="btn" style="background: #32cd32; color: white;">
                            <i class="fas fa-plus"></i> Добавить
                        </button>
                    </form>
                </div>
            </div>
            
            <div id="settings" class="tab-content">
                <h3><i class="fas fa-cog"></i> Настройки системы</h3>
                
                <form method="POST" action="/admin/update_settings" style="margin-top: 20px;">
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; color: #90ee90;">
                            <i class="fas fa-gift"></i> Бесплатный лимит
                        </label>
                        <input type="number" name="free_limit" value="{{ free_limit }}" min="1" max="100" 
                               style="width: 100%; padding: 12px; background: rgba(0,0,0,0.3); 
                               border: 1px solid #2a5c2a; color: #e8f5e8; border-radius: 8px;">
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; color: #90ee90;">
                            <i class="fas fa-crown"></i> PRO лимит
                        </label>
                        <input type="number" name="pro_limit" value="{{ pro_limit }}" min="10" max="10000"
                               style="width: 100%; padding: 12px; background: rgba(0,0,0,0.3); 
                               border: 1px solid #2a5c2a; color: #e8f5e8; border-radius: 8px;">
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; color: #90ee90;">
                            <i class="fas fa-key"></i> Пароль админа
                        </label>
                        <input type="text" name="admin_password" value="{{ admin_password }}"
                               style="width: 100%; padding: 12px; background: rgba(0,0,0,0.3); 
                               border: 1px solid #2a5c2a; color: #e8f5e8; border-radius: 8px;">
                    </div>
                    
                    <button type="submit" class="btn" style="background: #32cd32; color: white; width: 100%; padding: 12px;">
                        <i class="fas fa-save"></i> Сохранить настройки
                    </button>
                </form>
            </div>
        </div>
        {% endif %}
    </div>
    
    {% if logged_in %}
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.currentTarget.classList.add('active');
        }
        
        function searchUsers() {
            const search = document.getElementById('userSearch').value.toLowerCase();
            const users = document.querySelectorAll('.user-item');
            
            users.forEach(user => {
                const text = user.textContent.toLowerCase();
                user.style.display = text.includes(search) ? 'flex' : 'none';
            });
        }
        
        function togglePro(userId, makePro) {
            if (confirm(makePro ? `Сделать пользователя ${userId} PRO?` : `Убрать PRO у пользователя ${userId}?`)) {
                fetch(`/admin/toggle_pro/${userId}?make_pro=${makePro}`, {
                    method: 'POST'
                }).then(() => location.reload());
            }
        }
        
        function deleteUser(userId) {
            if (confirm(`Удалить пользователя ${userId}?`)) {
                fetch(`/admin/delete_user/${userId}`, {
                    method: 'DELETE'
                }).then(() => location.reload());
            }
        }
    </script>
    {% endif %}
</body>
</html>
'''

# Инициализация базы данных
if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

# Загружаем пользователей
users_db = load_users()

# Утилиты
def get_user_id():
    """Получаем или создаем ID пользователя"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
    
    # Создаем запись пользователя если нет
    if user_id not in users_db:
        users_db[user_id] = {
            'requests_today': 0,
            'last_request_date': datetime.now().date().isoformat(),
            'is_pro': False,
            'pro_until': None,
            'created_date': datetime.now().date().isoformat(),
            'limit': FREE_LIMIT
        }
        save_users(users_db)
    
    return user_id

def check_request_limit(user_id):
    """Проверяем лимит запросов для пользователя"""
    user = users_db.get(user_id)
    if not user:
        return True, FREE_LIMIT, 0
    
    today = datetime.now().date()
    last_date = datetime.fromisoformat(user['last_request_date']).date()
    
    # Сбрасываем счетчик если новый день
    if last_date != today:
        user['requests_today'] = 0
        user['last_request_date'] = today.isoformat()
        save_users(users_db)
    
    # Определяем лимит
    limit = user['limit'] if user['is_pro'] else FREE_LIMIT
    
    return user['requests_today'] < limit, limit, user['requests_today']

def increment_request_count(user_id):
    """Увеличиваем счетчик запросов"""
    user = users_db.get(user_id)
    if user:
        user['requests_today'] += 1
        user['last_request_date'] = datetime.now().date().isoformat()
        save_users(users_db)

# Улучшенные роли для GPT-4
DEFAULT_ROLES = {
    "assistant": """Ты - Mateus AI, сверхразумный помощник на основе GPT-4 Turbo. 
    Отвечай подробно, глубоко и с креативным подходом. 
    Используй эмодзи для выразительности. 
    Предлагай дополнительные идеи и перспективы.
    Будь максимально полезным и информативным.""",
    
    "psychologist": """Ты - ведущий психолог с докторской степенью, эксперт в когнитивно-поведенческой терапии, 
    нейропсихологии и эмоциональном интеллекте. 
    Давай научно обоснованные советы, предлагай практические упражнения.
    Будь эмпатичным, профессиональным и поддерживающим.""",
    
    "teacher": """Ты - профессор университета с 20-летним опытом преподавания.
    Объясняй сложные концепции простыми словами с аналогиями и примерами.
    Задавай наводящие вопросы для лучшего понимания.
    Предоставляй структурированную информацию по шагам.""",
    
    "programmer": """Ты - senior разработчик уровня Google/Facebook.
    Помогай с архитектурой, оптимизацией, best practices.
    Пиши чистый, эффективный код с комментариями.
    Объясняй алгоритмы и паттерны проектирования.
    Предлагай несколько решений с плюсами/минусами."""
}

# Хранилище сессий
session_roles = {}
session_histories = {}

# Основные маршруты
@app.route('/')
def index():
    """Главная страница"""
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used = check_request_limit(user_id)
    
    current_time = datetime.now().strftime("%H:%M")
    
    return render_template_string(HTML_TEMPLATE,
        current_time=current_time,
        free_limit=FREE_LIMIT,
        pro_limit=PRO_LIMIT,
        is_pro=user.get('is_pro', False),
        requests_used=used,
        requests_limit=limit,
        remaining_requests=limit - used
    )

@app.route('/set_role', methods=['POST'])
def set_role():
    """Установка роли"""
    try:
        data = request.get_json()
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        role_type = data.get('role_type', 'assistant')
        role_description = data.get('role_description', '')
        
        if role_type in DEFAULT_ROLES:
            session_roles[session_id] = DEFAULT_ROLES[role_type]
        else:
            session_roles[session_id] = role_description
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    """Обработка сообщений"""
    try:
        user_id = get_user_id()
        
        # Проверяем лимит
        can_request, limit, used = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': 'limit_exceeded',
                'message': 'Лимит запросов исчерпан'
            })
        
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Empty message'})
        
        session_id = session.get('session_id')
        current_role = session_roles.get(session_id, DEFAULT_ROLES['assistant'])
        
        # Формируем историю
        messages = [{"role": "system", "content": current_role}]
        
        if session_id in session_histories:
            for msg in session_histories[session_id][-6:]:
                role = "user" if msg['sender'] == 'user' else "assistant"
                messages.append({"role": role, "content": msg['text']})
        
        messages.append({"role": "user", "content": user_message})
        
        # Вызываем OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        response_text = response.choices[0].message.content
        
        # Сохраняем историю
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
        
        # Обрезаем историю
        if len(session_histories[session_id]) > 20:
            session_histories[session_id] = session_histories[session_id][-20:]
        
        # Увеличиваем счетчик
        increment_request_count(user_id)
        can_request, limit, used = check_request_limit(user_id)
        
        return jsonify({
            'success': True,
            'response': response_text,
            'requests_used': used,
            'requests_limit': limit
        })
        
    except openai.error.OpenAIError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Очистка истории"""
    session_id = session.get('session_id')
    if session_id in session_histories:
        session_histories[session_id] = []
    return jsonify({'success': True})

# Админ маршруты
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    """Админ-панель"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            return render_template_string(ADMIN_TEMPLATE, 
                logged_in=False, 
                error='Неверный логин или пароль'
            )
    
    if not session.get('admin_logged_in'):
        return render_template_string(ADMIN_TEMPLATE, logged_in=False)
    
    # Статистика
    total_users = len(users_db)
    pro_users = sum(1 for user in users_db.values() if user.get('is_pro'))
    active_users = sum(1 for user in users_db.values() if user.get('requests_today', 0) > 0)
    
    # Запросы сегодня
    today = datetime.now().date().isoformat()
    today_requests = sum(user.get('requests_today', 0) for user in users_db.values() 
                        if user.get('last_request_date') == today)
    
    # Статистика по дням
    daily_stats = {}
    for user in users_db.values():
        date = user.get('last_request_date')
        if date:
            daily_stats[date] = daily_stats.get(date, 0) + user.get('requests_today', 0)
    
    # Сортируем по дате
    daily_stats = dict(sorted(daily_stats.items(), reverse=True)[:7])
    max_requests = max(daily_stats.values()) if daily_stats else 1
    
    # Использование памяти
    import psutil
    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024 / 1024  # MB
    
    return render_template_string(ADMIN_TEMPLATE,
        logged_in=True,
        total_users=total_users,
        pro_users=pro_users,
        active_users=active_users,
        today_requests=today_requests,
        daily_stats=daily_stats,
        max_requests=max_requests,
        memory_usage=memory_usage,
        users=users_db,
        free_limit=FREE_LIMIT,
        pro_limit=PRO_LIMIT,
        admin_password=ADMIN_PASSWORD,
        message=request.args.get('message'),
        message_type=request.args.get('type')
    )

@app.route('/admin/toggle_pro/<user_id>', methods=['POST'])
def toggle_pro(user_id):
    """Включение/выключение PRO"""
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    make_pro = request.args.get('make_pro', 'true').lower() == 'true'
    
    if user_id in users_db:
        users_db[user_id]['is_pro'] = make_pro
        users_db[user_id]['limit'] = PRO_LIMIT if make_pro else FREE_LIMIT
        
        if make_pro:
            users_db[user_id]['pro_until'] = (datetime.now() + timedelta(days=30)).date().isoformat()
        else:
            users_db[user_id]['pro_until'] = None
        
        save_users(users_db)
    
    return redirect('/admin?message=PRO статус обновлен&type=success')

@app.route('/admin/delete_user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Удаление пользователя"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False})
    
    if user_id in users_db:
        del users_db[user_id]
        save_users(users_db)
    
    return jsonify({'success': True})

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    """Добавление пользователя"""
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    user_id = request.form.get('user_id')
    is_pro = request.form.get('is_pro') == 'true'
    limit = int(request.form.get('limit', FREE_LIMIT))
    
    if user_id and user_id not in users_db:
        users_db[user_id] = {
            'requests_today': 0,
            'last_request_date': datetime.now().date().isoformat(),
            'is_pro': is_pro,
            'pro_until': (datetime.now() + timedelta(days=30)).date().isoformat() if is_pro else None,
            'created_date': datetime.now().date().isoformat(),
            'limit': limit
        }
        save_users(users_db)
    
    return redirect('/admin?message=Пользователь добавлен&type=success')

@app.route('/admin/update_settings', methods=['POST'])
def update_settings():
    """Обновление настроек"""
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    global FREE_LIMIT, PRO_LIMIT, ADMIN_PASSWORD
    
    FREE_LIMIT = int(request.form.get('free_limit', 10))
    PRO_LIMIT = int(request.form.get('pro_limit', 1000))
    ADMIN_PASSWORD = request.form.get('admin_password', ADMIN_PASSWORD)
    
    # Обновляем лимиты у пользователей
    for user_id, user_data in users_db.items():
        if not user_data.get('is_pro'):
            user_data['limit'] = FREE_LIMIT
    
    save_users(users_db)
    
    return redirect('/admin?message=Настройки сохранены&type=success')

@app.route('/admin/logout')
def admin_logout():
    """Выход из админ-панели"""
    session.pop('admin_logged_in', None)
    return redirect('/admin')

@app.route('/health')
def health():
    """Проверка здоровья"""
    return jsonify({
        'status': 'healthy',
        'users': len(users_db),
        'openai_api': 'active' if openai.api_key else 'inactive',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    
    print("=" * 60)
    print("🤖 MATEUS AI - ЗАПУСК СЕРВЕРА")
    print("=" * 60)
    print(f"🔑 API ключ: {'✅ АКТИВЕН' if openai.api_key else '❌ НЕ АКТИВЕН'}")
    print(f"🔐 Админ пароль: {ADMIN_PASSWORD}")
    print(f"📊 Пользователей в БД: {len(users_db)}")
    print(f"👑 PRO пользователей: {sum(1 for u in users_db.values() if u.get('is_pro'))}")
    print(f"🎯 Бесплатный лимит: {FREE_LIMIT} запросов")
    print(f"👑 PRO лимит: {PRO_LIMIT} запросов")
    print(f"🌐 Порт: {port}")
    print(f"🚀 Запуск на: http://localhost:{port}")
    print(f"🔧 Админ-панель: http://localhost:{port}/admin")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
