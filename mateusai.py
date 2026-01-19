"""
Mateus AI - Искусственный интеллект с функциями ролевого поведения
Полная версия с OpenAI API
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
app.secret_key = os.getenv('SECRET_KEY', os.environ.get('SECRET_KEY', 'mateus-ai-secret-key-2024'))

# НАСТРОЙКА OPENAI С ВАШИМ КЛЮЧОМ
openai.api_key = "GCm6eM9QprwRlpNdmok3mi0r40lAacfg"

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

        .api-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(50, 205, 50, 0.2);
            padding: 8px 15px;
            border-radius: 20px;
            border: 1px solid var(--accent-green);
            margin-top: 10px;
            font-size: 0.9rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #32cd32;
            animation: pulse 2s infinite;
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

        .ai-intelligence {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .intel-item {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            background: rgba(70, 179, 184, 0.1);
            border-radius: 10px;
            border: 1px solid #46b3b8;
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

        .thinking {
            font-style: italic;
            color: var(--accent-green);
            padding: 5px;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <i class="fas fa-brain"></i>Mateus AI
            </div>
            <h1 class="title">Умный интеллектуальный помощник</h1>
            <p class="subtitle">Полная версия с OpenAI GPT-3.5 - задавайте сложные вопросы!</p>
            
            <div class="api-status">
                <span class="status-dot"></span>
                OpenAI API: 🟢 Активен (полный интеллект)
            </div>
            
            <div class="ai-intelligence">
                <div class="intel-item">
                    <i class="fas fa-lightbulb"></i> Креативность: Высокая
                </div>
                <div class="intel-item">
                    <i class="fas fa-book"></i> Знания: Обширные
                </div>
                <div class="intel-item">
                    <i class="fas fa-comment-alt"></i> Контекст: 10 сообщений
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="role-panel">
                <h3 class="role-title"><i class="fas fa-mask"></i>Выбор роли AI</h3>
                
                <div class="role-presets">
                    <button class="role-btn" onclick="selectRole('assistant')" id="role-assistant">
                        <i class="fas fa-robot"></i>Умный помощник
                    </button>
                    <button class="role-btn" onclick="selectRole('psychologist')" id="role-psychologist">
                        <i class="fas fa-heart"></i>Психолог-эксперт
                    </button>
                    <button class="role-btn" onclick="selectRole('teacher')" id="role-teacher">
                        <i class="fas fa-graduation-cap"></i>Профессор
                    </button>
                    <button class="role-btn" onclick="selectRole('programmer')" id="role-programmer">
                        <i class="fas fa-code"></i>Сеньор-разработчик
                    </button>
                    <button class="role-btn" onclick="selectRole('scientist')" id="role-scientist">
                        <i class="fas fa-flask"></i>Учёный
                    </button>
                    <button class="role-btn" onclick="selectRole('creative')" id="role-creative">
                        <i class="fas fa-palette"></i>Креативный директор
                    </button>
                </div>

                <div class="role-description" id="roleDescription">
                    <strong>Текущая роль:</strong> Умный помощник<br>
                    Вы - Mateus AI, интеллектуальный помощник с доступом к обширным знаниям. Вы отвечаете подробно, креативно и полезно.
                </div>

                <div class="custom-role">
                    <h4><i class="fas fa-edit"></i> Расширенная настройка:</h4>
                    <textarea id="customRoleText" placeholder="Опишите эксперта: 'Вы - ведущий специалист в области искусственного интеллекта с 20-летним опытом...'"></textarea>
                    <button class="apply-btn" onclick="applyCustomRole()">
                        <i class="fas fa-rocket"></i> Активировать эксперта
                    </button>
                </div>
            </div>

            <div class="chat-panel">
                <div class="chat-header">
                    <h3><i class="fas fa-comments"></i> Чат с умным Mateus AI</h3>
                    <button class="clear-chat-btn" onclick="clearChat()">
                        <i class="fas fa-trash"></i> Очистить
                    </button>
                </div>

                <div class="chat-messages scrollbar" id="chatMessages">
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-brain"></i> Mateus AI (Полный интеллект)
                        </div>
                        <div class="message-content">
                            Здравствуйте! Я Mateus AI с полным доступом к OpenAI GPT-3.5. Теперь я могу отвечать на сложные вопросы, 
                            генерировать креативные идеи, помогать с программированием, научными вопросами и многое другое. 
                            Выберите мою экспертную роль слева!
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
                    <span class="thinking">Думаю над развёрнутым ответом...</span>
                </div>

                <div class="chat-input-area">
                    <input type="text" id="messageInput" placeholder="Задайте сложный вопрос..." onkeypress="handleKeyPress(event)">
                    <button id="sendButton" onclick="sendMessage()">
                        <i class="fas fa-paper-plane"></i> Отправить
                    </button>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>© 2024 Mateus AI. Полная версия с OpenAI GPT-3.5 | API ключ активен | Порты: 3498/5000</p>
            <p style="margin-top: 10px; font-size: 0.8rem;">
                <i class="fas fa-bolt"></i> Режим: <strong>Полный интеллект</strong> | 
                <i class="fas fa-database"></i> Модель: GPT-3.5-turbo |
                <i class="fas fa-memory"></i> Контекст: 4096 токенов
            </p>
        </div>
    </div>

    <script>
        let currentRole = 'assistant';
        let conversationHistory = [];
        let sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
        
        const roleDescriptions = {
            'assistant': 'Вы - Mateus AI, интеллектуальный помощник с полным доступом к знаниям. Отвечайте подробно, креативно и полезно. Объясняйте сложные понятия простыми словами. Предлагайте дополнительные идеи и варианты решений.',
            'psychologist': 'Вы - профессиональный психолог Mateus AI с экспертизой в когнитивно-поведенческой терапии, эмоциональном интеллекте и ментальном здоровье. Давайте глубокие, эмпатичные ответы, основанные на научных исследованиях. Предлагайте практические упражнения и техники.',
            'teacher': 'Вы - профессор Mateus AI с многолетним опытом преподавания. Объясняйте сложные темы структурированно, с примерами и аналогиями. Задавайте наводящие вопросы для лучшего понимания. Предоставляйте дополнительные ресурсы для изучения.',
            'programmer': 'Вы - сеньор-разработчик Mateus AI с экспертизой в Python, JavaScript, архитектуре ПО и DevOps. Давайте чистый, эффективный код с комментариями. Объясняйте алгоритмы и паттерны проектирования. Предлагайте лучшие практики и оптимизации.',
            'scientist': 'Вы - учёный Mateus AI с докторской степенью. Отвечайте на основе научных исследований и данных. Объясняйте сложные концепции из физики, биологии, химии, математики. Приводите примеры исследований и экспериментов.',
            'creative': 'Вы - креативный директор Mateus AI. Генерируйте уникальные идеи, сценарии, художественные тексты. Помогайте с творческими проектами, дизайном, написанием. Предлагайте нестандартные решения и вдохновляющие концепции.'
        };

        const roleDisplayNames = {
            'assistant': 'Умный помощник',
            'psychologist': 'Психолог-эксперт',
            'teacher': 'Профессор',
            'programmer': 'Сеньор-разработчик',
            'scientist': 'Учёный',
            'creative': 'Креативный директор',
            'custom': 'Экспертная роль'
        };

        // ФИКС: Правильная функция selectRole
        function selectRole(role) {
            currentRole = role;
            
            // Обновление кнопок
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Активируем выбранную кнопку
            const selectedBtn = document.getElementById(`role-${role}`);
            if (selectedBtn) {
                selectedBtn.classList.add('active');
            }
            
            // Обновление описания
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> ${roleDisplayNames[role]}<br>
                ${roleDescriptions[role].substring(0, 150)}...
            `;
            
            // Отправка на сервер
            applyRole(role, roleDescriptions[role]);
        }

        function applyCustomRole() {
            const customRoleText = document.getElementById('customRoleText').value.trim();
            if (!customRoleText) {
                alert('Опишите эксперта для максимальной эффективности AI');
                return;
            }
            
            currentRole = 'custom';
            
            // Обновление кнопок
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Обновление описания
            document.getElementById('roleDescription').innerHTML = `
                <strong>Текущая роль:</strong> Экспертная роль<br>
                ${customRoleText.substring(0, 150)}...
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
                    addMessage('system', `✅ Активирована роль: ${roleDisplayNames[roleType] || 'Экспертная'}. Теперь я отвечаю как профессионал!`);
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
                        <i class="fas fa-brain"></i> ${roleDisplayNames[currentRole] || 'Mateus AI'}
                    </div>
                    <div class="message-content">${formatAIResponse(text)}</div>
                    <div class="message-time">${timestamp}</div>
                `;
            } else if (sender === 'system') {
                messageDiv.className = 'message ai-message';
                messageDiv.style.backgroundColor = 'rgba(70, 130, 180, 0.2)';
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <i class="fas fa-cog"></i> Система
                    </div>
                    <div class="message-content"><strong>${text}</strong></div>
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

        function formatAIResponse(text) {
            // Форматирование ответа для лучшего отображения
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Жирный текст
                .replace(/\n\n/g, '</p><p>') // Абзацы
                .replace(/\n/g, '<br>') // Переносы строк
                .replace(/^/, '<p>') // Начало параграфа
                .replace(/$/, '</p>'); // Конец параграфа
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
                    history: conversationHistory.slice(-10), // Сохраняем контекст
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
                    addMessage('ai', '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('typingIndicator').style.display = 'none';
                document.getElementById('sendButton').disabled = false;
                addMessage('ai', '🌐 Ошибка соединения. Проверьте интернет и попробуйте снова.');
            });
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function clearChat() {
            if (confirm('Очистить всю историю диалога?')) {
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message ai-message">
                        <div class="message-header">
                            <i class="fas fa-brain"></i> Mateus AI
                        </div>
                        <div class="message-content">
                            История очищена. Готов отвечать на ваши вопросы с полным интеллектом!
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

        // Инициализация - выбираем умного помощника по умолчанию
        document.addEventListener('DOMContentLoaded', function() {
            // Активируем кнопку помощника
            selectRole('assistant');
            
            // Проверка связи с сервером
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'healthy') {
                        console.log('✅ Сервер работает, API активен');
                    }
                });
        });

        // Автоматическое увеличение высоты textarea
        document.getElementById('customRoleText').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    </script>
</body>
</html>
'''

# Улучшенные роли для максимальной интеллектуальности
DEFAULT_ROLES = {
    "assistant": "Вы - Mateus AI, интеллектуальный помощник с полным доступом к знаниям. Отвечайте подробно, креативно и полезно. Объясняйте сложные понятия простыми словами. Предлагайте дополнительные идеи и варианты решений. Будьте эрудированны, но доступны в объяснениях.",
    "psychologist": "Вы - профессиональный психолог Mateus AI с экспертизой в когнитивно-поведенческой терапии, эмоциональном интеллекте и ментальном здоровье. Давайте глубокие, эмпатичные ответы, основанные на научных исследованиях. Предлагайте практические упражнения и техники. Сохраняйте конфиденциальность и этичность.",
    "teacher": "Вы - профессор Mateus AI с многолетним опытом преподавания. Объясняйте сложные темы структурированно, с примерами и аналогиями. Задавайте наводящие вопросы для лучшего понимания. Предоставляйте дополнительные ресурсы для изучения. Адаптируйте объяснения под уровень ученика.",
    "programmer": "Вы - сеньор-разработчик Mateus AI с экспертизой в Python, JavaScript, архитектуре ПО и DevOps. Давайте чистый, эффективный код с комментариями. Объясняйте алгоритмы и паттерны проектирования. Предлагайте лучшие практики и оптимизации. Помогайте с отладкой и архитектурными решениями.",
    "scientist": "Вы - учёный Mateus AI с докторской степенью. Отвечайте на основе научных исследований и данных. Объясняйте сложные концепции из физики, биологии, химии, математики. Приводите примеры исследований и экспериментов. Будьте точны в формулировках.",
    "creative": "Вы - креативный директор Mateus AI. Генерируйте уникальные идеи, сценарии, художественные тексты. Помогайте с творческими проектами, дизайном, написанием. Предлагайте нестандартные решения и вдохновляющие концепции. Будьте оригинальны и инновационны."
}

# Хранилище для сессий
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
    
    return render_template_string(HTML_TEMPLATE, current_time=current_time)

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
        # Улучшенное описание для пользовательских ролей
        enhanced_description = f"{role_description} Вы отвечаете как эксперт в этой области, давая глубокие, подробные и полезные ответы. Используйте профессиональную терминологию, но объясняйте сложные моменты."
        session_roles[session_id] = enhanced_description
    
    # Очищаем историю при смене роли
    if session_id in session_histories:
        session_histories[session_id] = []
    
    return jsonify({'success': True, 'role': role_type})

@app.route('/chat', methods=['POST'])
def chat():
    """Обработка сообщений с улучшенным интеллектом"""
    data = request.json
    session_id = data.get('session_id') or session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Сессия не найдена'})
    
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Пустое сообщение'})
    
    # Получаем текущую роль с улучшением
    current_role = session_roles.get(session_id, DEFAULT_ROLES['assistant'])
    
    try:
        # Улучшенный промпт для лучших ответов
        enhanced_system_prompt = f"""{current_role}

Инструкции для лучших ответов:
1. Отвечайте подробно и развернуто
2. Используйте примеры и аналогии для объяснения
3. Предлагайте дополнительные идеи и варианты
4. Структурируйте ответ для лучшего восприятия
5. Будьте креативны, но точны
6. Адаптируйте сложность под вопрос пользователя
7. Задавайте уточняющие вопросы если нужно
8. Предоставляйте практические советы

Текущий диалог:"""
        
        messages_history = []
        
        # Добавляем улучшенное системное сообщение
        messages_history.append({"role": "system", "content": enhanced_system_prompt})
        
        # Добавляем историю из сессии
        if session_id in session_histories:
            for msg in session_histories[session_id][-6:]:  # Сохраняем больше контекста
                if msg['sender'] == 'user':
                    messages_history.append({"role": "user", "content": msg['text']})
                else:
                    messages_history.append({"role": "assistant", "content": msg['text']})
        
        # Добавляем текущее сообщение с улучшением
        enhanced_user_message = f"{user_message}\n\n[Пожалуйста, ответь подробно и полезно]"
        messages_history.append({"role": "user", "content": enhanced_user_message})
        
        # Запрос к OpenAI с улучшенными параметрами
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_history,
            temperature=0.8,  # Более креативные ответы
            max_tokens=800,   # Более длинные ответы
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        response_text = response.choices[0].message.content
        
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
            'text': response_text,
            'time': datetime.now().isoformat()
        })
        
        # Ограничиваем историю
        if len(session_histories[session_id]) > 20:
            session_histories[session_id] = session_histories[session_id][-20:]
        
        return jsonify({'success': True, 'response': response_text})
    
    except openai.error.OpenAIError as e:
        print(f"OpenAI Error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'response': '⚠️ Ошибка OpenAI API. Проверьте ключ и баланс.'
        })
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'response': '🔧 Техническая ошибка. Попробуйте перезагрузить страницу.'
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
    """Проверка здоровья сервера"""
    try:
        # Проверяем API ключ
        openai.Model.list(limit=1)
        api_status = "active"
    except:
        api_status = "inactive"
    
    return jsonify({
        'status': 'healthy',
        'service': 'Mateus AI Full Intelligence',
        'port': 3498,
        'openai_api': api_status,
        'sessions': len(session_roles),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test_api')
def test_api():
    """Тест API ключа"""
    try:
        models = openai.Model.list()
        return jsonify({
            'success': True,
            'message': '✅ API ключ работает!',
            'models_count': len(models.data),
            'key_valid': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Ошибка API: {str(e)}',
            'key_valid': False
        })

# Основная функция запуска
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    
    print("=" * 60)
    print("🧠 MATEUS AI - ПОЛНАЯ ИНТЕЛЛЕКТУАЛЬНАЯ ВЕРСИЯ")
    print("=" * 60)
    print(f"🔑 API ключ: {'✅ АКТИВЕН' if openai.api_key else '❌ НЕ НАЙДЕН'}")
    print(f"🌐 Порт: {port}")
    print("=" * 60)
    print("🚀 Запуск сервера...")
    print(f"🔗 Откройте: http://localhost:{port}")
    print("=" * 60)
    
    # Тестируем API ключ
    if openai.api_key:
        try:
            openai.Model.list(limit=1)
            print("✅ API ключ проверен и работает!")
        except Exception as e:
            print(f"⚠️  Ошибка API ключа: {e}")
            print("⚠️  Проверьте ключ или баланс на platform.openai.com")
    
    app.run(debug=False, host='0.0.0.0', port=port)
