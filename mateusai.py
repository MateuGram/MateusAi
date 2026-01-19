"""
Mateus AI - Улучшенная версия с исправленными ошибками и современным дизайном
"""

import os
import json
import uuid
import secrets
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect
import openai
from openai import OpenAI
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Инициализация OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    print("❌ ERROR: OPENAI_API_KEY environment variable is required!")
    exit(1)

client = OpenAI(api_key=openai.api_key)

# Конфигурация DonationAlerts
DONATION_ALERTS = {
    'client_id': os.environ.get('DA_CLIENT_ID', ''),
    'client_secret': os.environ.get('DA_CLIENT_SECRET', ''),
    'redirect_uri': os.environ.get('DA_REDIRECT_URI', 'http://localhost:3498/donation/callback'),
    'api_url': 'https://www.donationalerts.com/api/v1',
    'auth_url': 'https://www.donationalerts.com/oauth/authorize',
    'token_url': 'https://www.donationalerts.com/oauth/token'
}

# Лимиты
FREE_LIMIT = 10
PRO_LIMIT = 1000
PRO_PRICE = 1000  # рублей за месяц PRO

# Пароль админа
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Qwerty123Admin123")
if not ADMIN_PASSWORD:
    print("⚠️  Warning: ADMIN_PASSWORD not set. Using default insecure password")

# Файлы данных
USERS_FILE = 'users.json'
DONATIONS_FILE = 'donations.json'
SETTINGS_FILE = 'settings.json'

# ==================== УТИЛИТЫ ====================

def ensure_files_exist():
    """Создает файлы если они не существуют"""
    for filename in [USERS_FILE, DONATIONS_FILE, SETTINGS_FILE]:
        if not os.path.exists(filename):
            default_data = {}
            if filename == SETTINGS_FILE:
                default_data = {
                    'donation_alerts': {'connected': False, 'access_token': '', 'refresh_token': ''},
                    'pro_codes': {}
                }
            save_data(filename, default_data)
            print(f"📁 Created {filename}")

def load_data(filename, default={}):
    """Загрузка данных из файла с обработкой ошибок"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else default
    except json.JSONDecodeError:
        print(f"⚠️  Error decoding {filename}, returning default")
        return default
    except Exception as e:
        print(f"⚠️  Error loading {filename}: {e}")
        return default
    return default

def save_data(filename, data):
    """Сохранение данных в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return False

# Инициализация данных
ensure_files_exist()
users_db = load_data(USERS_FILE)
donations_db = load_data(DONATIONS_FILE)
settings_db = load_data(SETTINGS_FILE, {
    'donation_alerts': {'connected': False, 'access_token': '', 'refresh_token': ''},
    'pro_codes': {}
})

# ==================== HTML ШАБЛОНЫ ====================

BASE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #1a5d1a; 
            --secondary: #2e8b57;
            --light: #90ee90; 
            --accent: #32cd32;
            --dark: #0d3b0d; 
            --background: #0a1a0a;
            --card: #162416; 
            --text: #f0fff0;
            --muted: #a3d9a3; 
            --border: #2a5c2a;
            --gold: #ffd700; 
            --blue: #4dabf7;
            --purple: #9775fa; 
            --red: #ff6b6b;
            --pink: #f783ac;
            --gradient: linear-gradient(135deg, #1a5d1a, #2e8b57, #32cd32);
            --gradient-gold: linear-gradient(45deg, #ffd700, #ffaa00, #ff6b00);
            --gradient-purple: linear-gradient(45deg, #9775fa, #748ffc, #4dabf7);
        }
        
        body {
            font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
            background: var(--background);
            color: var(--text); 
            min-height: 100vh;
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.1;
            background: 
                radial-gradient(circle at 20% 30%, rgba(46, 139, 87, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(50, 205, 50, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(144, 238, 144, 0.05) 0%, transparent 50%);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        /* Шапка */
        .header {
            text-align: center;
            padding: 40px 30px;
            background: linear-gradient(135deg, rgba(26, 93, 26, 0.9), rgba(13, 59, 13, 0.9));
            border-radius: 24px;
            margin-bottom: 40px;
            border: 2px solid var(--accent);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, transparent 30%, rgba(144, 238, 144, 0.15) 70%);
            animation: pulse 20s infinite linear;
        }
        
        @keyframes pulse {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .logo {
            font-size: 4rem;
            margin-bottom: 20px;
            color: var(--light);
            text-shadow: 0 0 30px var(--accent),
                        0 0 60px rgba(50, 205, 50, 0.3);
            position: relative;
            z-index: 1;
            animation: glow 3s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 20px var(--light), 0 0 30px rgba(50, 205, 50, 0.3); }
            to { text-shadow: 0 0 30px var(--accent), 0 0 40px rgba(50, 205, 50, 0.5), 0 0 50px rgba(50, 205, 50, 0.2); }
        }
        
        .title {
            font-size: 3.2rem;
            margin-bottom: 15px;
            background: linear-gradient(45deg, var(--light), var(--accent), var(--gold));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
            z-index: 1;
            font-weight: 800;
        }
        
        .subtitle {
            font-size: 1.3rem;
            color: var(--muted);
            margin-bottom: 25px;
            position: relative;
            z-index: 1;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Основной контент */
        .main-content {
            display: grid;
            grid-template-columns: 1fr 3fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        @media (max-width: 1100px) {
            .main-content {
                grid-template-columns: 1fr;
                gap: 20px;
            }
        }
        
        /* Карточки */
        .card {
            background: linear-gradient(145deg, rgba(22, 36, 22, 0.9), rgba(13, 59, 13, 0.7));
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(42, 92, 42, 0.5);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2),
                        inset 0 1px 0 rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .card:hover {
            transform: translateY(-5px);
            border-color: var(--accent);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3),
                        0 0 30px rgba(50, 205, 50, 0.1);
        }
        
        /* Кнопки */
        .btn {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            color: white;
            padding: 14px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            text-decoration: none;
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s;
        }
        
        .btn:hover::before {
            left: 100%;
        }
        
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(46, 139, 87, 0.4);
            border-color: var(--accent);
        }
        
        .btn:active {
            transform: translateY(-1px);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--accent), var(--light));
            color: var(--dark);
        }
        
        .btn-pro {
            background: var(--gradient-gold);
            color: #222;
            font-weight: bold;
        }
        
        .btn-pro:hover {
            box-shadow: 0 10px 25px rgba(255, 170, 0, 0.4);
        }
        
        .btn-purple {
            background: var(--gradient-purple);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, var(--red), #ff4757);
            color: white;
        }
        
        .btn.active {
            background: linear-gradient(135deg, var(--secondary), var(--accent));
            border-color: var(--light);
            box-shadow: 0 0 20px rgba(50, 205, 50, 0.5),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        
        /* Статус бейджи */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.9rem;
            font-weight: 600;
            backdrop-filter: blur(5px);
        }
        
        .status-success {
            background: rgba(50, 205, 50, 0.15);
            color: var(--accent);
            border: 1px solid rgba(50, 205, 50, 0.3);
        }
        
        .status-warning {
            background: rgba(255, 215, 0, 0.15);
            color: var(--gold);
            border: 1px solid rgba(255, 215, 0, 0.3);
        }
        
        .status-error {
            background: rgba(255, 107, 107, 0.15);
            color: var(--red);
            border: 1px solid rgba(255, 107, 107, 0.3);
        }
        
        .status-info {
            background: rgba(77, 171, 247, 0.15);
            color: var(--blue);
            border: 1px solid rgba(77, 171, 247, 0.3);
        }
        
        /* Чат */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        .chat-messages {
            flex: 1;
            min-height: 500px;
            max-height: 600px;
            overflow-y: auto;
            margin-bottom: 25px;
            padding: 20px;
            background: rgba(13, 59, 13, 0.2);
            border-radius: 16px;
            border: 1px solid rgba(42, 92, 42, 0.3);
            scroll-behavior: smooth;
        }
        
        /* Стилизация скроллбара */
        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
            background: var(--accent);
            border-radius: 4px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: var(--light);
        }
        
        .message {
            margin-bottom: 20px;
            padding: 18px;
            border-radius: 18px;
            max-width: 85%;
            animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .user-message {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            margin-left: auto;
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .ai-message {
            background: linear-gradient(135deg, rgba(46, 139, 87, 0.2), rgba(32, 201, 151, 0.1));
            border: 1px solid rgba(42, 92, 42, 0.4);
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }
        
        .message-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .message-content {
            line-height: 1.6;
        }
        
        .message-time {
            text-align: right;
            font-size: 0.8rem;
            color: var(--muted);
            margin-top: 10px;
            opacity: 0.8;
        }
        
        .chat-input {
            display: flex;
            gap: 15px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 16px 20px;
            background: rgba(0, 0, 0, 0.2);
            border: 2px solid rgba(42, 92, 42, 0.5);
            border-radius: 12px;
            color: var(--text);
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .chat-input input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(50, 205, 50, 0.1);
            background: rgba(0, 0, 0, 0.3);
        }
        
        /* Секция ролей */
        .roles-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .role-card {
            background: rgba(22, 36, 22, 0.6);
            border: 1px solid rgba(42, 92, 42, 0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .role-card:hover {
            background: rgba(46, 139, 87, 0.2);
            border-color: var(--accent);
            transform: translateY(-3px);
        }
        
        .role-card.active {
            background: linear-gradient(135deg, rgba(46, 139, 87, 0.3), rgba(50, 205, 50, 0.2));
            border-color: var(--accent);
            box-shadow: 0 5px 15px rgba(50, 205, 50, 0.2);
        }
        
        .role-icon {
            font-size: 2rem;
            margin-bottom: 10px;
            color: var(--accent);
        }
        
        /* PRO секция */
        .pro-section {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, rgba(151, 117, 250, 0.1), rgba(116, 143, 252, 0.05));
            border-radius: 16px;
            border: 1px solid rgba(151, 117, 250, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .pro-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-purple);
        }
        
        .pro-badge {
            background: var(--gradient-gold);
            color: #222;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.8rem;
            margin-left: 10px;
            display: inline-block;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .feature {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        
        /* Админ ссылка */
        .admin-link {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 107, 107, 0.15);
            color: var(--red);
            padding: 10px 18px;
            border-radius: 12px;
            text-decoration: none;
            border: 1px solid rgba(255, 107, 107, 0.3);
            z-index: 2;
            transition: all 0.3s ease;
        }
        
        .admin-link:hover {
            background: rgba(255, 107, 107, 0.25);
            transform: translateY(-2px);
        }
        
        /* Уведомления */
        .alert {
            padding: 18px;
            margin: 15px 0;
            border-radius: 12px;
            border-left: 4px solid;
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(5px);
        }
        
        .alert-success {
            border-color: var(--accent);
            background: rgba(50, 205, 50, 0.1);
        }
        
        .alert-warning {
            border-color: var(--gold);
            background: rgba(255, 215, 0, 0.1);
        }
        
        .alert-error {
            border-color: var(--red);
            background: rgba(255, 107, 107, 0.1);
        }
        
        .alert-info {
            border-color: var(--blue);
            background: rgba(77, 171, 247, 0.1);
        }
        
        /* Формы */
        .code-input {
            width: 100%;
            padding: 16px;
            margin: 15px 0;
            background: rgba(0, 0, 0, 0.2);
            border: 2px solid rgba(42, 92, 42, 0.5);
            border-radius: 12px;
            color: var(--text);
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .code-input:focus {
            outline: none;
            border-color: var(--purple);
            box-shadow: 0 0 0 3px rgba(151, 117, 250, 0.1);
        }
        
        /* Подвал */
        .footer {
            text-align: center;
            padding: 30px 20px;
            color: var(--muted);
            border-top: 1px solid rgba(42, 92, 42, 0.3);
            margin-top: 40px;
            backdrop-filter: blur(5px);
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 25px;
            margin-top: 15px;
        }
        
        .footer-links a {
            color: var(--accent);
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .footer-links a:hover {
            color: var(--light);
            text-decoration: underline;
        }
        
        /* Анимации */
        .fade-in {
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Прогресс бар */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--gradient);
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        
        /* Адаптивность */
        @media (max-width: 768px) {
            .header {
                padding: 25px 20px;
            }
            
            .logo {
                font-size: 3rem;
            }
            
            .title {
                font-size: 2.2rem;
            }
            
            .main-content {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .chat-input {
                flex-direction: column;
            }
            
            .message {
                max-width: 95%;
            }
            
            .roles-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 480px) {
            .header {
                padding: 20px 15px;
            }
            
            .logo {
                font-size: 2.5rem;
            }
            
            .title {
                font-size: 1.8rem;
            }
            
            .card {
                padding: 20px;
            }
            
            .roles-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="container">
        {header}
        <div class="main-content fade-in">
            {sidebar}
            {content}
        </div>
        {footer}
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Инициализация ролей
            document.querySelectorAll('.role-card').forEach(card => {
                card.onclick = function() {
                    document.querySelectorAll('.role-card').forEach(c => c.classList.remove('active'));
                    this.classList.add('active');
                    selectRole(this.dataset.role);
                };
            });
            
            // Отправка сообщений
            window.sendMessage = function() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Показываем анимацию отправки
                const sendBtn = document.querySelector('.chat-input .btn');
                const originalHtml = sendBtn.innerHTML;
                sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                sendBtn.disabled = true;
                
                // Добавляем сообщение пользователя
                addMessage('user', message);
                input.value = '';
                
                // Отправляем на сервер
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        addMessage('ai', data.response);
                        updateUsage(data.usage || {});
                    } else {
                        addMessage('ai', `<div class="alert alert-error">${data.error || 'Ошибка соединения'}</div>`);
                    }
                })
                .catch(error => {
                    addMessage('ai', `<div class="alert alert-error">Ошибка сети: ${error.message}</div>`);
                })
                .finally(() => {
                    sendBtn.innerHTML = originalHtml;
                    sendBtn.disabled = false;
                    input.focus();
                });
            };
            
            // Enter для отправки
            document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Активация PRO кода
            window.activatePro = function() {
                const code = document.getElementById('proCode').value.trim();
                if (!code) {
                    showAlert('Введите код активации', 'warning');
                    return;
                }
                
                const btn = document.getElementById('activateProBtn');
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                btn.disabled = true;
                
                fetch('/activate_pro', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({code: code})
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        showAlert(data.message, 'success');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showAlert(data.message, 'error');
                    }
                })
                .finally(() => {
                    btn.innerHTML = originalHtml;
                    btn.disabled = false;
                });
            };
            
            // Плавная прокрутка
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const targetId = this.getAttribute('href');
                    if (targetId === '#') return;
                    
                    const targetElement = document.querySelector(targetId);
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        });
        
        function selectRole(role) {
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role: role})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showAlert(`Роль "${role}" активирована`, 'success');
                }
            });
        }
        
        function addMessage(sender, text) {
            const chat = document.getElementById('chatMessages');
            if (!chat) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const senderName = sender === 'user' ? '👤 Вы' : '🤖 Mateus AI';
            const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <i class="${icon}"></i>
                    <span>${senderName}</span>
                </div>
                <div class="message-content">${text}</div>
                <div class="message-time">
                    ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </div>
            `;
            
            chat.appendChild(messageDiv);
            chat.scrollTo({
                top: chat.scrollHeight,
                behavior: 'smooth'
            });
        }
        
        function showAlert(message, type = 'info') {
            // Удаляем старые алерты
            document.querySelectorAll('.floating-alert').forEach(el => el.remove());
            
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} floating-alert`;
            alertDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                max-width: 400px;
                animation: slideInRight 0.3s ease;
            `;
            alertDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                    <div>${message}</div>
                </div>
            `;
            
            document.body.appendChild(alertDiv);
            
            setTimeout(() => {
                alertDiv.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => alertDiv.remove(), 300);
            }, 3000);
        }
        
        function updateUsage(usage) {
            const usageElement = document.getElementById('usageInfo');
            if (usageElement && usage.used !== undefined && usage.limit !== undefined) {
                const percent = (usage.used / usage.limit) * 100;
                usageElement.innerHTML = `
                    <div style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>Использовано: ${usage.used}/${usage.limit}</span>
                            <span>${Math.round(percent)}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percent}%"></div>
                        </div>
                    </div>
                `;
            }
        }
        
        // Добавляем стили для анимации алертов
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
'''

def render_page(title, header, sidebar, content, footer):
    """Рендер страницы"""
    return render_template_string(
        BASE_HTML,
        title=title,
        header=header,
        sidebar=sidebar,
        content=content,
        footer=footer
    )

# ==================== УТИЛИТЫ ====================

def get_user_id():
    """Получаем ID пользователя"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
    
    # Создаем запись если нет
    if user_id not in users_db:
        users_db[user_id] = {
            'id': user_id,
            'created': datetime.now().isoformat(),
            'requests_today': 0,
            'last_request': datetime.now().date().isoformat(),
            'is_pro': False,
            'pro_until': None,
            'pro_code': None,
            'limit': FREE_LIMIT,
            'total_requests': 0,
            'role': 'assistant'
        }
        save_data(USERS_FILE, users_db)
    
    return user_id

def check_request_limit(user_id):
    """Проверка лимита запросов"""
    if not users_db or user_id not in users_db:
        get_user_id()
    
    user = users_db.get(user_id, {})
    
    # Сброс счетчика если новый день
    today = datetime.now().date().isoformat()
    if user.get('last_request') != today:
        user['requests_today'] = 0
        user['last_request'] = today
        save_data(USERS_FILE, users_db)
    
    limit = PRO_LIMIT if user.get('is_pro') else FREE_LIMIT
    user['limit'] = limit
    
    return user['requests_today'] < limit, limit, user['requests_today']

def increment_request(user_id):
    """Увеличение счетчика запросов"""
    user = users_db.get(user_id)
    if user:
        user['requests_today'] = user.get('requests_today', 0) + 1
        user['total_requests'] = user.get('total_requests', 0) + 1
        user['last_request'] = datetime.now().date().isoformat()
        save_data(USERS_FILE, users_db)

def generate_pro_code():
    """Генерация безопасного кода для PRO"""
    return f"PRO-{secrets.token_hex(4).upper()}"

# Роли AI с улучшенными промптами
ROLES = {
    'assistant': {
        'name': 'Помощник',
        'prompt': 'Ты - умный и дружелюбный помощник Mateus AI. Отвечай подробно, полезно и понятно. Поддерживай позитивный тон и будь готов помочь с любыми вопросами.',
        'icon': 'fas fa-robot',
        'color': '#32cd32'
    },
    'psychologist': {
        'name': 'Психолог',
        'prompt': 'Ты - опытный психолог с эмпатией и пониманием. Помогай с эмоциональными вопросами, давай поддержку и практические советы. Сохраняй конфиденциальность и профессиональный подход.',
        'icon': 'fas fa-heart',
        'color': '#ff6b6b'
    },
    'teacher': {
        'name': 'Учитель',
        'prompt': 'Ты - терпеливый и знающий учитель. Объясняй сложные темы простыми словами, используй примеры и аналогии. Поощряй вопросы и помогай в обучении.',
        'icon': 'fas fa-graduation-cap',
        'color': '#4dabf7'
    },
    'programmer': {
        'name': 'Программист',
        'prompt': 'Ты - senior разработчик с опытом работы в разных технологиях. Помогай с кодом, архитектурой, отладкой и лучшими практиками. Будь точным и предлагай эффективные решения.',
        'icon': 'fas fa-code',
        'color': '#9775fa'
    },
    'scientist': {
        'name': 'Учёный',
        'prompt': 'Ты - учёный с критическим мышлением. Объясняй научные концепции точно и ясно, используй данные и исследования. Будь объективным и честным в ответах.',
        'icon': 'fas fa-flask',
        'color': '#ffd700'
    }
}

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    """Главная страница"""
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used = check_request_limit(user_id)
    remaining = limit - used
    percent_used = (used / limit * 100) if limit > 0 else 0
    
    # Текущая роль
    current_role = session.get('current_role', 'assistant')
    role_info = ROLES.get(current_role, ROLES['assistant'])
    
    # Шапка с улучшенным дизайном
    header = f'''
    <div class="header">
        <a href="/admin" class="admin-link">
            <i class="fas fa-cog"></i> Админ
        </a>
        <div class="logo"><i class="fas fa-brain-circuit"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p class="subtitle">Интеллектуальный помощник нового поколения</p>
        
        <div style="margin-top: 25px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
            <span class="status-badge {'status-success' if can_request else 'status-warning'}">
                <i class="fas fa-{'rocket' if can_request else 'hourglass-half'}"></i>
                Запросов: {used}/{limit}
            </span>
            
            <span class="status-badge status-info">
                <i class="{role_info['icon']}" style="color: {role_info['color']}"></i>
                Роль: {role_info['name']}
            </span>
            
            {'<span class="pro-badge"><i class="fas fa-crown"></i> PRO АКТИВНО</span>' if user.get('is_pro') else ''}
            
            {f'<span class="status-badge status-success"><i class="fas fa-calendar-star"></i> PRO до {datetime.fromisoformat(user.get("pro_until")).strftime("%d.%m.%Y")}</span>' if user.get('is_pro') and user.get('pro_until') else ''}
        </div>
        
        <div id="usageInfo" style="max-width: 600px; margin: 20px auto 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.9rem;">
                <span>Использовано: <strong>{used}/{limit}</strong></span>
                <span>Осталось: <strong>{remaining}</strong></span>
                <span>{percent_used:.1f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {percent_used}%"></div>
            </div>
        </div>
    </div>
    '''
    
    # Боковая панель с ролями
    sidebar = f'''
    <div class="card">
        <h3 style="color: var(--light); margin-bottom: 25px; display: flex; align-items: center; gap: 10px;">
            <i class="fas fa-mask"></i> Выберите роль
        </h3>
        
        <p style="color: var(--muted); margin-bottom: 20px; font-size: 0.95rem;">
            Каждая роль имеет уникальный стиль общения и экспертизу
        </p>
        
        <div class="roles-grid">
            {''.join([f'''
            <div class="role-card {'active' if role_id == current_role else ''}" 
                 data-role="{role_id}"
                 style="border-color: {role_data['color']}">
                <div class="role-icon">
                    <i class="{role_data['icon']}" style="color: {role_data['color']}"></i>
                </div>
                <div style="font-weight: 600; margin-bottom: 5px;">{role_data['name']}</div>
            </div>
            ''' for role_id, role_data in ROLES.items()])}
        </div>
        
        <div class="pro-section fade-in">
            <h4 style="color: var(--purple); margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-crown"></i> PRO Подписка
            </h4>
            
            <div class="features-grid">
                <div class="feature">
                    <i class="fas fa-bolt" style="color: var(--gold);"></i>
                    <span>{PRO_LIMIT} запросов/день</span>
                </div>
                <div class="feature">
                    <i class="fas fa-star" style="color: var(--purple);"></i>
                    <span>Приоритетная обработка</span>
                </div>
                <div class="feature">
                    <i class="fas fa-magic" style="color: var(--accent);"></i>
                    <span>Расширенный контекст</span>
                </div>
                <div class="feature">
                    <i class="fas fa-shield-alt" style="color: var(--blue);"></i>
                    <span>Без рекламы</span>
                </div>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 2rem; font-weight: bold; color: var(--gold);">
                    {PRO_PRICE} ₽
                </div>
                <div style="color: var(--muted); font-size: 0.9rem;">/ 30 дней</div>
            </div>
            
            <input type="text" id="proCode" class="code-input" placeholder="Введите код активации">
            <button id="activateProBtn" class="btn btn-pro" onclick="activatePro()" style="width: 100%;">
                <i class="fas fa-bolt"></i> Активировать PRO
            </button>
            
            <div style="text-align: center; margin-top: 15px;">
                <a href="/donation_info" class="btn btn-purple" style="padding: 10px 20px;">
                    <i class="fas fa-donate"></i> Получить код
                </a>
            </div>
        </div>
    </div>
    '''
    
    # Основной контент - чат
    content = f'''
    <div class="card">
        <div class="chat-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                <h3 style="color: var(--light); display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-comments"></i> Чат с Mateus AI
                </h3>
                <span class="status-badge status-info">
                    <i class="{role_info['icon']}" style="color: {role_info['color']}"></i>
                    {role_info['name']}
                </span>
            </div>
            
            <div id="chatMessages" class="chat-messages">
                <div class="ai-message">
                    <div class="message-header">
                        <i class="fas fa-robot"></i>
                        <span>🤖 Mateus AI</span>
                    </div>
                    <div class="message-content">
                        <p>Привет! Я Mateus AI — ваш умный помощник. 😊</p>
                        <p>Я могу помочь вам с различными задачами:</p>
                        <ul style="margin: 10px 0 10px 20px;">
                            <li>Ответить на вопросы любой сложности</li>
                            <li>Помочь с программированием и технологиями</li>
                            <li>Объяснить научные концепции</li>
                            <li>Поддержать в психологических вопросах</li>
                            <li>И многое другое!</li>
                        </ul>
                        <p>Выберите роль слева для специализированной помощи или просто спросите меня о чём угодно!</p>
                    </div>
                    <div class="message-time">
                        {datetime.now().strftime("%H:%M")}
                    </div>
                </div>
            </div>
            
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Введите ваш вопрос... (Нажмите Enter для отправки)" autofocus>
                <button class="btn btn-primary" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i> Отправить
                </button>
            </div>
            
            <div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;">
                <div class="status-badge status-info" onclick="document.getElementById('messageInput').value = 'Расскажи о своих возможностях'">
                    <i class="fas fa-lightbulb"></i> Возможности
                </div>
                <div class="status-badge status-info" onclick="document.getElementById('messageInput').value = 'Как получить PRO версию?'">
                    <i class="fas fa-crown"></i> PRO
                </div>
                <div class="status-badge status-info" onclick="document.getElementById('messageInput').value = 'Приведи пример кода на Python'">
                    <i class="fas fa-code"></i> Код
                </div>
                <div class="status-badge status-info" onclick="document.getElementById('messageInput').value = 'Объясни теорию относительности просто'">
                    <i class="fas fa-atom"></i> Наука
                </div>
            </div>
        </div>
    </div>
    '''
    
    # Подвал
    footer = f'''
    <div class="footer">
        <p>© 2024 Mateus AI | Искусственный интеллект нового поколения</p>
        <div class="footer-links">
            <a href="/donation_info"><i class="fas fa-donate"></i> Поддержать проект</a>
            <a href="/admin"><i class="fas fa-cog"></i> Админ-панель</a>
            <a href="#" onclick="showAlert('Версия 2.0 | OpenAI GPT-3.5 Turbo', 'info')"><i class="fas fa-info-circle"></i> О системе</a>
        </div>
        <p style="margin-top: 15px; font-size: 0.9rem; color: rgba(163, 217, 163, 0.6);">
            Бесплатно: {FREE_LIMIT} запросов/день | PRO: {PRO_LIMIT} запросов/день
        </p>
    </div>
    '''
    
    return render_page('Mateus AI - Умный помощник', header, sidebar, content, footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    """Установка роли"""
    try:
        data = request.get_json()
        role = data.get('role', 'assistant')
        
        if role in ROLES:
            session['current_role'] = role
            user_id = get_user_id()
            if user_id in users_db:
                users_db[user_id]['role'] = role
                save_data(USERS_FILE, users_db)
            
            return jsonify({
                'success': True, 
                'message': f'Роль "{ROLES[role]["name"]}" активирована',
                'role_name': ROLES[role]['name']
            })
        
        return jsonify({'success': False, 'error': 'Неизвестная роль'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    """Обработка сообщений"""
    try:
        user_id = get_user_id()
        
        # Проверка лимита
        can_request, limit, used = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': f'⚠️ Лимит запросов исчерпан ({used}/{limit}).<br>Для увеличения лимита приобретите PRO подписку!'
            })
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})
        
        # Получаем роль
        role = session.get('current_role', 'assistant')
        role_data = ROLES.get(role, ROLES['assistant'])
        system_prompt = role_data['prompt']
        
        # Добавляем контекст для PRO пользователей
        user = users_db.get(user_id, {})
        if user.get('is_pro'):
            system_prompt += "\n\n[PRO-ПОЛЬЗОВАТЕЛЬ] Пользователь имеет активную PRO подписку. Отвечай максимально подробно, профессионально и используй расширенные возможности."
        
        # Добавляем контекст лимитов
        remaining = limit - used
        system_prompt += f"\n\n[КОНТЕКСТ] У пользователя осталось {remaining} запросов из {limit} на сегодня."
        
        try:
            # Запрос к OpenAI с новой версией API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=800,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            answer = response.choices[0].message.content
            
            # Увеличиваем счетчик
            increment_request(user_id)
            
            # Получаем обновленные данные об использовании
            _, new_limit, new_used = check_request_limit(user_id)
            
            return jsonify({
                'success': True, 
                'response': answer,
                'usage': {
                    'used': new_used,
                    'limit': new_limit,
                    'remaining': new_limit - new_used
                }
            })
            
        except openai.RateLimitError:
            return jsonify({
                'success': False,
                'error': '⏳ Превышен лимит запросов к OpenAI. Пожалуйста, попробуйте через несколько минут.'
            })
        except openai.AuthenticationError:
            return jsonify({
                'success': False,
                'error': '🔑 Ошибка аутентификации с OpenAI API. Пожалуйста, свяжитесь с администратором.'
            })
        except openai.APIError as e:
            return jsonify({
                'success': False,
                'error': f'🌐 Ошибка API: {str(e)}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'⚠️ Ошибка обработки запроса: {str(e)}'
            })
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера. Пожалуйста, попробуйте позже.'
        })

@app.route('/activate_pro', methods=['POST'])
def activate_pro():
    """Активация PRO кода"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return jsonify({'success': False, 'message': 'Введите код активации'})
        
        user_id = get_user_id()
        
        # Проверяем код
        if code in settings_db.get('pro_codes', {}):
            pro_data = settings_db['pro_codes'][code]
            
            if pro_data.get('used'):
                return jsonify({'success': False, 'message': 'Код уже использован'})
            
            if pro_data.get('expires') and datetime.fromisoformat(pro_data['expires']) < datetime.now():
                return jsonify({'success': False, 'message': 'Срок действия кода истёк'})
            
            # Активируем PRO
            user = users_db[user_id]
            days = 30
            if 'days' in pro_data:
                days = pro_data['days']
            
            user['is_pro'] = True
            user['pro_until'] = (datetime.now() + timedelta(days=days)).isoformat()
            user['pro_code'] = code
            user['limit'] = PRO_LIMIT
            
            # Помечаем код как использованный
            pro_data['used'] = True
            pro_data['used_by'] = user_id
            pro_data['used_at'] = datetime.now().isoformat()
            
            save_data(USERS_FILE, users_db)
            save_data(SETTINGS_FILE, settings_db)
            
            return jsonify({
                'success': True, 
                'message': f'🎉 PRO подписка активирована на {days} дней! Теперь у вас {PRO_LIMIT} запросов в день.'
            })
        
        return jsonify({'success': False, 'message': 'Неверный код активации'})
    
    except Exception as e:
        print(f"Activate PRO error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка при активации кода'})

@app.route('/donation_info')
def donation_info():
    """Информация о донатах"""
    user_id = session.get('user_id', 'Неизвестен')
    
    content = f'''
    <div class="card fade-in">
        <h2 style="color: var(--light); margin-bottom: 25px; display: flex; align-items: center; gap: 15px;">
            <i class="fas fa-crown"></i> Получение PRO Подписки
        </h2>
        
        <div class="alert alert-success" style="margin-bottom: 25px;">
            <h3 style="margin-bottom: 10px;"><i class="fas fa-gift"></i> Что даёт PRO подписка?</h3>
            <ul style="margin: 10px 0 10px 20px;">
                <li><strong>{PRO_LIMIT} запросов в день</strong> (вместо {FREE_LIMIT} бесплатных)</li>
                <li>Приоритетная обработка запросов</li>
                <li>Расширенный контекст разговора</li>
                <li>Доступ ко всем экспертным ролям</li>
                <li>Более детальные и развернутые ответы</li>
                <li>Отсутствие рекламы и ограничений</li>
            </ul>
        </div>
        
        <div class="alert alert-warning" style="margin-bottom: 25px;">
            <h3 style="margin-bottom: 10px;"><i class="fas fa-ruble-sign"></i> Стоимость</h3>
            <div style="text-align: center; padding: 15px;">
                <div style="font-size: 2.5rem; font-weight: bold; color: var(--gold);">
                    {PRO_PRICE} рублей
                </div>
                <div style="color: var(--muted);">за 30 дней использования</div>
            </div>
        </div>
        
        <div class="alert alert-info" style="margin-bottom: 25px;">
            <h3 style="margin-bottom: 10px;"><i class="fas fa-qrcode"></i> Как получить PRO?</h3>
            <ol style="margin: 15px 0 15px 25px; line-height: 1.8;">
                <li><strong>Сделайте донат {PRO_PRICE} рублей</strong> через DonationAlerts</li>
                <li>В комментарии к донату укажите ваш ID: <code style="background: rgba(0,0,0,0.3); padding: 3px 8px; border-radius: 4px; font-weight: bold;">{user_id}</code></li>
                <li>После проверки доната (обычно в течение 24 часов) вам будет выдан PRO код</li>
                <li>Введите полученный код в поле активации на главной странице</li>
                <li>Наслаждайтесь всеми преимуществами PRO подписки!</li>
            </ol>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="/" class="btn btn-primary" style="padding: 15px 30px; font-size: 1.1rem;">
                <i class="fas fa-arrow-left"></i> Вернуться на главную
            </a>
        </div>
    </div>
    '''
    
    return render_page(
        'Получение PRO подписки',
        '<div class="header"><div class="logo"><i class="fas fa-crown"></i></div><h1 class="title">PRO Подписка</h1></div>',
        '',
        content,
        '<div class="footer"><p>© 2024 Mateus AI</p></div>'
    )

# ==================== АДМИН ПАНЕЛЬ ====================

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Админ-панель Mateus AI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --admin-bg: #0a0a1a;
            --admin-card: #15152e;
            --admin-border: #2a2a5c;
            --admin-text: #e8e8ff;
            --admin-muted: #a3a3d9;
            --admin-primary: #4d4dff;
            --admin-success: #32cd32;
            --admin-warning: #ffd700;
            --admin-danger: #ff4757;
            --admin-purple: #9775fa;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #15152e 100%);
            color: var(--admin-text);
            min-height: 100vh;
            padding: 20px;
        }
        
        .admin-container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .admin-header {
            text-align: center;
            padding: 40px 30px;
            background: linear-gradient(135deg, rgba(77, 77, 255, 0.1), rgba(151, 117, 250, 0.1));
            border-radius: 20px;
            margin-bottom: 40px;
            border: 2px solid var(--admin-primary);
            position: relative;
            overflow: hidden;
        }
        
        .admin-header h1 {
            font-size: 2.8rem;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #4d4dff, #9775fa);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .admin-card {
            background: var(--admin-card);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--admin-border);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }
        
        .admin-card:hover {
            transform: translateY(-5px);
            border-color: var(--admin-primary);
        }
        
        .admin-card h2 {
            color: var(--admin-text);
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 2px solid var(--admin-border);
            padding-bottom: 15px;
        }
        
        .btn {
            background: linear-gradient(135deg, var(--admin-primary), #6c63ff);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(77, 77, 255, 0.4);
        }
        
        .btn-success {
            background: linear-gradient(135deg, var(--admin-success), #2ecc71);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, var(--admin-warning), #ff9f43);
            color: #333;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, var(--admin-danger), #ff3838);
        }
        
        .btn-small {
            padding: 8px 16px;
            font-size: 0.9rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
            color: var(--admin-primary);
        }
        
        .stat-label {
            color: var(--admin-muted);
            font-size: 0.9rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid var(--admin-border);
        }
        
        th {
            background: rgba(77, 77, 255, 0.1);
            color: var(--admin-primary);
            font-weight: 600;
        }
        
        tr:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .badge-success {
            background: rgba(50, 205, 50, 0.2);
            color: var(--admin-success);
            border: 1px solid rgba(50, 205, 50, 0.3);
        }
        
        .badge-warning {
            background: rgba(255, 215, 0, 0.2);
            color: var(--admin-warning);
            border: 1px solid rgba(255, 215, 0, 0.3);
        }
        
        .badge-danger {
            background: rgba(255, 71, 87, 0.2);
            color: var(--admin-danger);
            border: 1px solid rgba(255, 71, 87, 0.3);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid var(--admin-border);
            border-radius: 8px;
            color: var(--admin-text);
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--admin-primary);
            box-shadow: 0 0 0 3px rgba(77, 77, 255, 0.1);
        }
        
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: var(--admin-card);
            border-radius: 20px;
            border: 2px solid var(--admin-border);
            text-align: center;
        }
        
        .login-container h2 {
            margin-bottom: 30px;
            color: var(--admin-primary);
        }
        
        .alert {
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid;
        }
        
        .alert-success {
            background: rgba(50, 205, 50, 0.1);
            border-color: var(--admin-success);
            color: var(--admin-success);
        }
        
        .alert-error {
            background: rgba(255, 71, 87, 0.1);
            border-color: var(--admin-danger);
            color: var(--admin-danger);
        }
        
        .search-box {
            margin-bottom: 20px;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid var(--admin-border);
            border-radius: 10px;
            color: var(--admin-text);
            font-size: 1rem;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        
        .page-btn {
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--admin-border);
            border-radius: 6px;
            color: var(--admin-text);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .page-btn:hover {
            background: rgba(77, 77, 255, 0.1);
            border-color: var(--admin-primary);
        }
        
        .page-btn.active {
            background: var(--admin-primary);
            color: white;
        }
    </style>
</head>
<body>
    <div class="admin-container">
        {% if not logged_in %}
        <div class="login-container">
            <h2><i class="fas fa-lock"></i> Админ-панель</h2>
            <form method="POST">
                <div class="form-group">
                    <input type="password" name="password" class="form-control" placeholder="Пароль администратора" required>
                </div>
                <button type="submit" class="btn" style="width: 100%;">
                    <i class="fas fa-sign-in-alt"></i> Войти
                </button>
            </form>
            {% if error %}
            <div class="alert alert-error" style="margin-top: 20px;">
                <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            {% endif %}
        </div>
        {% else %}
        
        <div class="admin-header">
            <h1><i class="fas fa-cogs"></i> Админ-панель Mateus AI</h1>
            <p style="color: var(--admin-muted); margin-bottom: 20px;">Управление системой и пользователями</p>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <a href="/" class="btn btn-small"><i class="fas fa-home"></i> На главную</a>
                <a href="/admin/logout" class="btn btn-danger btn-small"><i class="fas fa-sign-out-alt"></i> Выйти</a>
            </div>
        </div>
        
        {% if message %}
        <div class="alert alert-{{ message_type }}" style="margin-bottom: 30px;">
            <i class="fas fa-{{ 'check-circle' if message_type == 'success' else 'exclamation-triangle' }}"></i>
            {{ message }}
        </div>
        {% endif %}
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label"><i class="fas fa-users"></i> Всего пользователей</div>
                <div class="stat-value">{{ users_total }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label"><i class="fas fa-crown"></i> PRO пользователей</div>
                <div class="stat-value">{{ pro_users }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label"><i class="fas fa-comments"></i> Запросов сегодня</div>
                <div class="stat-value">{{ requests_today }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label"><i class="fas fa-ticket-alt"></i> Активных кодов</div>
                <div class="stat-value">{{ active_codes }}</div>
            </div>
        </div>
        
        <div class="admin-card">
            <h2><i class="fas fa-users-cog"></i> Управление пользователями</h2>
            
            <div class="search-box">
                <input type="text" id="userSearch" placeholder="Поиск пользователей...">
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>PRO</th>
                        <th>Запросы</th>
                        <th>Дата регистрации</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user_id, user in users.items() %}
                    <tr class="user-row">
                        <td>
                            <div style="font-weight: 600;">{{ user_id[:8] }}...</div>
                            <div style="font-size: 0.8rem; color: var(--admin-muted);">{{ user.get('role', 'assistant') }}</div>
                        </td>
                        <td>
                            {% if user.is_pro %}
                            <span class="badge badge-success">PRO</span>
                            {% if user.pro_until %}
                            <div style="font-size: 0.8rem; margin-top: 5px;">до {{ user.pro_until[:10] }}</div>
                            {% endif %}
                            {% else %}
                            <span class="badge badge-warning">FREE</span>
                            {% endif %}
                        </td>
                        <td>
                            <div>{{ user.requests_today }}/{{ user.limit }}</div>
                            <div style="font-size: 0.8rem; color: var(--admin-muted);">всего: {{ user.get('total_requests', 0) }}</div>
                        </td>
                        <td>{{ user.created[:10] if user.created else 'N/A' }}</td>
                        <td>
                            <div style="display: flex; gap: 8px;">
                                {% if user.is_pro %}
                                <button class="btn btn-warning btn-small" onclick="togglePro('{{ user_id }}', false)">
                                    <i class="fas fa-times"></i> Убрать PRO
                                </button>
                                {% else %}
                                <button class="btn btn-success btn-small" onclick="togglePro('{{ user_id }}', true)">
                                    <i class="fas fa-crown"></i> Дать PRO
                                </button>
                                {% endif %}
                                <button class="btn btn-danger btn-small" onclick="deleteUser('{{ user_id }}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="admin-card">
            <h2><i class="fas fa-ticket-alt"></i> Управление PRO кодами</h2>
            
            <form method="POST" action="/admin/create_code" style="margin-bottom: 25px;">
                <div style="display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 15px; align-items: end;">
                    <div class="form-group">
                        <label style="display: block; margin-bottom: 8px; color: var(--admin-muted);">Дней действия</label>
                        <input type="number" name="days" class="form-control" value="30" min="1" max="365">
                    </div>
                    <div class="form-group">
                        <label style="display: block; margin-bottom: 8px; color: var(--admin-muted);">Примечание</label>
                        <input type="text" name="note" class="form-control" placeholder="Например: Донат от пользователя">
                    </div>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-plus"></i> Создать код
                    </button>
                </div>
            </form>
            
            <h3 style="margin-bottom: 20px; color: var(--admin-muted);">Список кодов</h3>
            <table>
                <thead>
                    <tr>
                        <th>Код</th>
                        <th>Срок действия</th>
                        <th>Статус</th>
                        <th>Использован</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {% for code, data in pro_codes.items() %}
                    <tr>
                        <td><code style="font-weight: bold;">{{ code }}</code></td>
                        <td>{{ data.expires[:10] if data.expires else '∞' }}</td>
                        <td>
                            {% if data.used %}
                            <span class="badge badge-success">Использован</span>
                            {% else %}
                            <span class="badge badge-warning">Активен</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if data.used %}
                            {{ data.used_by[:8] }}...<br>
                            <small>{{ data.used_at[:16] if data.used_at else '' }}</small>
                            {% else %}
                            —
                            {% endif %}
                        </td>
                        <td>
                            {% if not data.used %}
                            <button class="btn btn-danger btn-small" onclick="deleteCode('{{ code }}')">
                                <i class="fas fa-trash"></i> Удалить
                            </button>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="admin-card">
            <h2><i class="fas fa-donate"></i> DonationAlerts</h2>
            
            {% if donation_connected %}
            <div style="margin-bottom: 25px;">
                <span class="badge badge-success" style="margin-bottom: 15px; display: inline-block;">
                    <i class="fas fa-check"></i> Подключено
                </span>
                <p style="color: var(--admin-muted); margin-bottom: 20px;">
                    Токен: <code>{{ donation_token[:30] }}...</code><br>
                    Подключено: {{ settings_db.get('donation_alerts', {}).get('connected_at', '')[:10] }}
                </p>
                
                <form method="POST" action="/admin/check_donations">
                    <button type="submit" class="btn">
                        <i class="fas fa-sync"></i> Проверить новые донаты
                    </button>
                </form>
            </div>
            {% else %}
            <div style="margin-bottom: 25px;">
                <span class="badge badge-danger" style="margin-bottom: 15px; display: inline-block;">
                    <i class="fas fa-times"></i> Не подключено
                </span>
                <p style="color: var(--admin-muted); margin-bottom: 20px;">
                    Подключите DonationAlerts для автоматической выдачи PRO кодов
                </p>
                <a href="/admin/connect_da" class="btn">
                    <i class="fas fa-plug"></i> Подключить DonationAlerts
                </a>
            </div>
            {% endif %}
        </div>
        
        <script>
            // Поиск пользователей
            document.getElementById('userSearch')?.addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                document.querySelectorAll('.user-row').forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
            
            // Управление PRO статусом
            function togglePro(userId, makePro) {
                if (confirm(makePro ? 'Выдать PRO подписку пользователю?' : 'Отменить PRO подписку?')) {
                    fetch(`/admin/toggle_pro/${userId}?make_pro=${makePro}`, {
                        method: 'POST',
                        headers: {'X-Requested-With': 'XMLHttpRequest'}
                    })
                    .then(() => location.reload());
                }
            }
            
            // Удаление пользователя
            function deleteUser(userId) {
                if (confirm('Удалить пользователя? Это действие нельзя отменить.')) {
                    fetch(`/admin/delete_user/${userId}`, {
                        method: 'DELETE',
                        headers: {'X-Requested-With': 'XMLHttpRequest'}
                    })
                    .then(() => location.reload());
                }
            }
            
            // Удаление кода
            function deleteCode(code) {
                if (confirm('Удалить код? Это действие нельзя отменить.')) {
                    fetch(`/admin/delete_code/${code}`, {
                        method: 'DELETE',
                        headers: {'X-Requested-With': 'XMLHttpRequest'}
                    })
                    .then(() => location.reload());
                }
            }
        </script>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Админ-панель"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
        else:
            return render_template_string(ADMIN_HTML, 
                logged_in=False, 
                error='Неверный пароль'
            )
    
    if not session.get('admin'):
        return render_template_string(ADMIN_HTML, logged_in=False)
    
    # Статистика
    users_total = len(users_db)
    pro_users = sum(1 for u in users_db.values() if u.get('is_pro'))
    requests_today = sum(u.get('requests_today', 0) for u in users_db.values())
    
    # PRO коды
    pro_codes = settings_db.get('pro_codes', {})
    active_codes = sum(1 for c in pro_codes.values() if not c.get('used'))
    
    # DonationAlerts статус
    donation_connected = settings_db.get('donation_alerts', {}).get('connected', False)
    donation_token = settings_db.get('donation_alerts', {}).get('access_token', '')
    
    # Параметры сообщения
    message = request.args.get('message')
    message_type = request.args.get('type', 'success')
    
    return render_template_string(ADMIN_HTML,
        logged_in=True,
        users_total=users_total,
        pro_users=pro_users,
        requests_today=requests_today,
        active_codes=active_codes,
        users=users_db,
        pro_codes=pro_codes,
        donation_connected=donation_connected,
        donation_token=donation_token,
        settings_db=settings_db,
        message=message,
        message_type=message_type
    )

@app.route('/admin/toggle_pro/<user_id>', methods=['POST'])
def admin_toggle_pro(user_id):
    """Включение/выключение PRO"""
    if not session.get('admin'):
        return jsonify({'success': False})
    
    make_pro = request.args.get('make_pro', 'true').lower() == 'true'
    
    if user_id in users_db:
        users_db[user_id]['is_pro'] = make_pro
        users_db[user_id]['limit'] = PRO_LIMIT if make_pro else FREE_LIMIT
        if make_pro:
            days = int(request.args.get('days', 30))
            users_db[user_id]['pro_until'] = (datetime.now() + timedelta(days=days)).isoformat()
        else:
            users_db[user_id]['pro_until'] = None
            users_db[user_id]['pro_code'] = None
        
        save_data(USERS_FILE, users_db)
    
    return jsonify({'success': True})

@app.route('/admin/create_code', methods=['POST'])
def create_pro_code():
    """Создание PRO кода"""
    if not session.get('admin'):
        return redirect('/admin')
    
    days = int(request.form.get('days', 30))
    note = request.form.get('note', '').strip()
    code = generate_pro_code()
    
    settings_db.setdefault('pro_codes', {})[code] = {
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=days)).isoformat(),
        'used': False,
        'price': PRO_PRICE,
        'note': note,
        'created_by': 'admin'
    }
    
    save_data(SETTINGS_FILE, settings_db)
    
    return redirect(f'/admin?message=Код создан: {code}&type=success')

@app.route('/admin/delete_code/<code>', methods=['DELETE'])
def delete_pro_code(code):
    """Удаление PRO кода"""
    if not session.get('admin'):
        return jsonify({'success': False})
    
    if code in settings_db.get('pro_codes', {}):
        del settings_db['pro_codes'][code]
        save_data(SETTINGS_FILE, settings_db)
    
    return jsonify({'success': True})

@app.route('/admin/delete_user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Удаление пользователя"""
    if not session.get('admin'):
        return jsonify({'success': False})
    
    if user_id in users_db:
        del users_db[user_id]
        save_data(USERS_FILE, users_db)
    
    return jsonify({'success': True})

@app.route('/admin/connect_da')
def connect_donation_alerts():
    """Подключение DonationAlerts"""
    if not session.get('admin'):
        return redirect('/admin')
    
    if not DONATION_ALERTS['client_id']:
        return redirect('/admin?message=DonationAlerts client_id не настроен&type=error')
    
    # Параметры для OAuth
    params = {
        'client_id': DONATION_ALERTS['client_id'],
        'redirect_uri': DONATION_ALERTS['redirect_uri'],
        'response_type': 'code',
        'scope': 'oauth-donation-index oauth-user-show'
    }
    
    auth_url = f"{DONATION_ALERTS['auth_url']}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/donation/callback')
def donation_callback():
    """Callback от DonationAlerts"""
    code = request.args.get('code')
    
    if code:
        # Получаем токен
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': DONATION_ALERTS['client_id'],
            'client_secret': DONATION_ALERTS['client_secret'],
            'redirect_uri': DONATION_ALERTS['redirect_uri']
        }
        
        try:
            response = requests.post(DONATION_ALERTS['token_url'], data=token_data)
            if response.status_code == 200:
                token_info = response.json()
                
                # Сохраняем токен
                settings_db['donation_alerts'] = {
                    'connected': True,
                    'access_token': token_info.get('access_token'),
                    'refresh_token': token_info.get('refresh_token'),
                    'expires_in': token_info.get('expires_in'),
                    'connected_at': datetime.now().isoformat()
                }
                save_data(SETTINGS_FILE, settings_db)
                
                return redirect('/admin?message=DonationAlerts успешно подключён&type=success')
        except Exception as e:
            print(f"DonationAlerts connection error: {e}")
    
    return redirect('/admin?message=Ошибка подключения DonationAlerts&type=error')

@app.route('/admin/check_donations', methods=['POST'])
def check_donations():
    """Проверка новых донатов"""
    if not session.get('admin'):
        return redirect('/admin')
    
    access_token = settings_db.get('donation_alerts', {}).get('access_token')
    if not access_token:
        return redirect('/admin?message=DonationAlerts не подключен&type=error')
    
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{DONATION_ALERTS['api_url']}/alerts/donations?page=1", headers=headers)
        
        if response.status_code == 200:
            donations = response.json().get('data', [])
            processed_count = 0
            
            for donation in donations[:20]:  # Последние 20 донатов
                donation_id = donation.get('id')
                amount = donation.get('amount')
                message = donation.get('message', '')
                username = donation.get('username')
                created_at = donation.get('created_at')
                
                # Проверяем, не обрабатывали ли мы уже этот донат
                if str(donation_id) in donations_db:
                    continue
                
                # Проверяем донат на PRO_PRICE рублей
                if amount >= PRO_PRICE:
                    # Ищем ID пользователя в сообщении
                    import re
                    user_match = re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', message)
                    
                    if user_match:
                        user_id = user_match.group()
                        if user_id in users_db and not users_db[user_id].get('is_pro'):
                            # Даём PRO
                            users_db[user_id]['is_pro'] = True
                            users_db[user_id]['pro_until'] = (datetime.now() + timedelta(days=30)).isoformat()
                            users_db[user_id]['limit'] = PRO_LIMIT
                            
                            # Создаем код
                            code = generate_pro_code()
                            settings_db.setdefault('pro_codes', {})[code] = {
                                'created': datetime.now().isoformat(),
                                'expires': (datetime.now() + timedelta(days=30)).isoformat(),
                                'used': True,
                                'used_by': user_id,
                                'used_at': datetime.now().isoformat(),
                                'donation_id': donation_id,
                                'amount': amount,
                                'username': username,
                                'note': f'Донат от {username}'
                            }
                            
                            processed_count += 1
                    
                    # Сохраняем информацию о донате
                    donations_db[str(donation_id)] = {
                        'id': donation_id,
                        'amount': amount,
                        'message': message,
                        'username': username,
                        'created_at': created_at,
                        'processed': user_match is not None,
                        'processed_at': datetime.now().isoformat()
                    }
            
            if processed_count > 0:
                save_data(USERS_FILE, users_db)
                save_data(SETTINGS_FILE, settings_db)
                save_data(DONATIONS_FILE, donations_db)
                
                return redirect(f'/admin?message=Обработано {processed_count} новых донатов, PRO выданы&type=success')
            else:
                return redirect('/admin?message=Новых донатов для обработки не найдено&type=info')
        else:
            return redirect('/admin?message=Ошибка при получении донатов&type=error')
    
    except Exception as e:
        print(f"Ошибка проверки донатов: {e}")
        return redirect('/admin?message=Ошибка проверки донатов&type=error')

@app.route('/admin/logout')
def admin_logout():
    """Выход из админки"""
    session.pop('admin', None)
    return redirect('/admin')

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    
    # Создание файлов если их нет
    ensure_files_exist()
    
    print("=" * 70)
    print("🚀 MATEUS AI - ЗАПУСК СЕРВЕРА (УЛУЧШЕННАЯ ВЕРСИЯ)")
    print("=" * 70)
    print(f"🔑 OpenAI API: {'✅ Настроен' if openai.api_key else '❌ ОШИБКА: Не настроен'}")
    print(f"🔐 Админ пароль: {'✅ Настроен' if ADMIN_PASSWORD else '⚠️  Внимание: Используется пароль по умолчанию'}")
    print(f"💰 PRO цена: {PRO_PRICE} руб. / {PRO_LIMIT} запросов в день")
    print(f"🎯 Лимиты: FREE={FREE_LIMIT}, PRO={PRO_LIMIT}")
    print(f"👥 Пользователей в базе: {len(users_db)}")
    print(f"🌐 Порт: {port}")
    print(f"🚀 Запуск: http://localhost:{port}")
    print(f"🔧 Админка: http://localhost:{port}/admin")
    print("=" * 70)
    print("📝 Роли AI:")
    for role_id, role_data in ROLES.items():
        print(f"   • {role_data['name']}: {role_data['prompt'][:50]}...")
    print("=" * 70)
    
    # Запуск сервера
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,
        threaded=True
    )
