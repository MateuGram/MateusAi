import os
import json
import time
import hashlib
import requests
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from bs4 import BeautifulSoup
import pytz
import re
import logging

# Конфигурация
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-super-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mateus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Инициализация БД
db = SQLAlchemy(app)

# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    tokens = db.Column(db.Integer, default=100)
    subscription = db.Column(db.String(20), default='free')
    daily_requests = db.Column(db.Integer, default=0)
    last_request_date = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdminSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_password = db.Column(db.String(200), nullable=False)

# Создание таблиц
with app.app_context():
    db.create_all()
    # Создаем администратора по умолчанию
    if not AdminSettings.query.first():
        admin = AdminSettings(admin_password=generate_password_hash(
            os.environ.get('ADMIN_PASSWORD', 'MateusAdmin2024!')
        ))
        db.session.add(admin)
        db.session.commit()

# Утилиты для поиска в интернете
class InternetSearcher:
    @staticmethod
    def search_web(query, num_results=5):
        """Поиск информации в интернете"""
        try:
            # Используем DuckDuckGo через HTML парсинг
            url = f"https://html.duckduckgo.com/html/?q={query}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for result in soup.find_all('a', class_='result__url', limit=num_results):
                title = result.text.strip()
                link = result.get('href')
                if link and title:
                    results.append({'title': title, 'link': link})
            
            return results[:num_results]
        except:
            return []

    @staticmethod
    def get_page_content(url):
        """Получение содержимого веб-страницы"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Ограничиваем объем
        except:
            return ""

    @staticmethod
    def get_current_time():
        """Получение текущего времени из интернета"""
        try:
            response = requests.get('http://worldtimeapi.org/api/timezone/Europe/Moscow', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['datetime']
        except:
            pass
        return datetime.now().isoformat()

# ИИ обработчик
class MateusAI:
    def __init__(self):
        self.searcher = InternetSearcher()
        
    def process_query(self, query, user_context=None):
        """Основная обработка запроса"""
        # Получаем время
        current_time = self.searcher.get_current_time()
        
        # Проверяем специальные запросы
        if any(word in query.lower() for word in ['время', 'дата', 'сейчас', 'time', 'date']):
            return self._format_time_response(current_time)
        
        # Ищем информацию в интернете
        search_results = self.searcher.search_web(query, 3)
        
        # Анализируем результаты
        analyzed_info = self._analyze_results(query, search_results)
        
        # Формируем ответ
        response = self._generate_response(query, analyzed_info, current_time)
        
        return response
    
    def _analyze_results(self, query, results):
        """Анализ и сравнение информации из найденных источников"""
        analyzed = []
        
        for result in results:
            try:
                content = self.searcher.get_page_content(result['link'])
                if content:
                    # Простой анализ релевантности
                    query_words = set(query.lower().split())
                    content_words = set(content.lower().split())
                    common_words = query_words.intersection(content_words)
                    relevance = len(common_words) / len(query_words) if query_words else 0
                    
                    analyzed.append({
                        'title': result['title'],
                        'relevance': relevance,
                        'content': content[:1000],
                        'source': result['link']
                    })
            except:
                continue
        
        # Сортируем по релевантности
        analyzed.sort(key=lambda x: x['relevance'], reverse=True)
        return analyzed
    
    def _generate_response(self, query, analyzed_info, current_time):
        """Генерация финального ответа"""
        if not analyzed_info:
            return {
                'answer': f"🔍 По запросу '{query}' я не нашел достаточной информации в открытых источниках. Попробуйте переформулировать вопрос или задать более конкретный запрос.",
                'sources': [],
                'confidence': 'low'
            }
        
        # Берем самый релевантный источник
        best_source = analyzed_info[0]
        
        # Формируем ответ
        answer = f"🤖 **Mateus AI отвечает:**\n\n"
        answer += f"На основе анализа информации из интернета, вот что я нашел по вашему запросу '{query}':\n\n"
        
        # Краткое изложение
        summary = best_source['content'][:500] + "..." if len(best_source['content']) > 500 else best_source['content']
        answer += f"📝 **Основная информация:** {summary}\n\n"
        
        # Добавляем источники
        answer += "📚 **Источники информации:**\n"
        for i, source in enumerate(analyzed_info[:2], 1):
            answer += f"{i}. {source['title']}\n"
        
        # Добавляем время
        answer += f"\n🕒 *Информация актуальна на: {current_time[:19]}*"
        
        return {
            'answer': answer,
            'sources': [s['source'] for s in analyzed_info[:3]],
            'confidence': 'high' if best_source['relevance'] > 0.3 else 'medium'
        }
    
    def _format_time_response(self, time_str):
        """Форматирование ответа с временем"""
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        moscow_tz = pytz.timezone('Europe/Moscow')
        dt_moscow = dt.astimezone(moscow_tz)
        
        return {
            'answer': f"🕒 **Текущее время и дата:**\n\n"
                     f"📅 Дата: {dt_moscow.strftime('%d.%m.%Y')}\n"
                     f"⏰ Время: {dt_moscow.strftime('%H:%M:%S')}\n"
                     f"🌍 Часовой пояс: Москва (UTC+3)\n\n"
                     f"*Информация получена из интернета*",
            'sources': [],
            'confidence': 'high'
        }

# Инициализация ИИ
ai = MateusAI()

# Декораторы
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'error': 'Требуются права администратора'}), 403
        return f(*args, **kwargs)
    return decorated_function

def check_daily_limit(user):
    """Проверка дневного лимита запросов"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user.last_request_date != today:
        user.daily_requests = 0
        user.last_request_date = today
        db.session.commit()
    
    max_requests = 34 if user.subscription == 'free' else 1000
    
    if user.daily_requests >= max_requests:
        return False
    
    user.daily_requests += 1
    db.session.commit()
    return True

# HTML шаблоны
MAIN_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI - Нейросеть для ваших запросов</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --neon-green: #00ff88;
            --dark-green: #003320;
            --black: #000000;
            --gray: #111111;
            --light-gray: #222222;
        }
        
        body {
            background-color: var(--black);
            color: white;
            font-family: 'Roboto', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Анимации */
        @keyframes glow {
            0%, 100% { text-shadow: 0 0 10px var(--neon-green), 0 0 20px var(--neon-green); }
            50% { text-shadow: 0 0 20px var(--neon-green), 0 0 40px var(--neon-green); }
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        @keyframes pulse {
            0% { opacity: 0.4; }
            50% { opacity: 1; }
            100% { opacity: 0.4; }
        }
        
        /* Header */
        header {
            text-align: center;
            padding: 40px 20px;
            position: relative;
        }
        
        .logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 3.5em;
            font-weight: 900;
            color: var(--neon-green);
            animation: glow 3s infinite;
            margin-bottom: 10px;
        }
        
        .slogan {
            font-size: 1.2em;
            color: #aaa;
            margin-bottom: 30px;
        }
        
        .user-info {
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--gray);
            padding: 10px 20px;
            border-radius: 20px;
            border: 1px solid var(--neon-green);
        }
        
        /* Основной контент */
        .main-content {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 30px;
            margin-top: 30px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        /* Чат */
        .chat-container {
            background: var(--gray);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid var(--neon-green);
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.1);
        }
        
        .chat-messages {
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: var(--black);
            border-radius: 15px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        
        .message {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 15px;
            max-width: 80%;
            animation: float 2s infinite;
        }
        
        .user-message {
            background: linear-gradient(135deg, var(--dark-green), #005533);
            margin-left: auto;
            border: 1px solid var(--neon-green);
        }
        
        .ai-message {
            background: linear-gradient(135deg, #222, #333);
            margin-right: auto;
            border: 1px solid #444;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px;
            background: var(--black);
            border: 2px solid var(--neon-green);
            border-radius: 10px;
            color: white;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        button {
            padding: 15px 30px;
            background: linear-gradient(45deg, var(--dark-green), var(--neon-green));
            border: none;
            border-radius: 10px;
            color: black;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Orbitron', sans-serif;
        }
        
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        }
        
        /* Панель информации */
        .info-panel {
            background: var(--gray);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid var(--neon-green);
        }
        
        .stats {
            background: var(--black);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 10px 0;
            border-bottom: 1px solid #333;
        }
        
        .neon-text {
            color: var(--neon-green);
            font-weight: bold;
        }
        
        .loader {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .loader-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: var(--neon-green);
            border-radius: 50%;
            margin: 0 5px;
            animation: pulse 1.5s infinite;
        }
        
        .loader-dot:nth-child(2) { animation-delay: 0.2s; }
        .loader-dot:nth-child(3) { animation-delay: 0.4s; }
        
        /* Футер */
        footer {
            text-align: center;
            padding: 40px 20px;
            margin-top: 50px;
            border-top: 1px solid #333;
            color: #666;
        }
        
        /* Модальные окна */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
        }
        
        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--gray);
            padding: 40px;
            border-radius: 20px;
            border: 2px solid var(--neon-green);
            min-width: 400px;
        }
        
        .close-modal {
            position: absolute;
            top: 20px;
            right: 20px;
            color: var(--neon-green);
            cursor: pointer;
            font-size: 24px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #aaa;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            background: var(--black);
            border: 1px solid #444;
            border-radius: 8px;
            color: white;
        }
        
        .error {
            color: #ff4444;
            margin-top: 10px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">MATEUS AI</div>
            <div class="slogan">Нейросеть для ваших запросов</div>
            <div class="user-info" id="userInfo">
                <!-- Информация о пользователе -->
            </div>
        </header>
        
        <div class="main-content">
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="message ai-message">
                        🤖 Добро пожаловать в Mateus AI! Я ищу информацию в интернете, анализирую и предоставляю точные ответы. Спросите меня о чем угодно!
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="userInput" placeholder="Задайте ваш вопрос...">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
                
                <div class="loader" id="loader">
                    <div class="loader-dot"></div>
                    <div class="loader-dot"></div>
                    <div class="loader-dot"></div>
                    <br>Ищу информацию в интернете...
                </div>
            </div>
            
            <div class="info-panel">
                <div class="stats">
                    <h3 style="color: var(--neon-green); margin-bottom: 20px;">📊 Ваша статистика</h3>
                    <div class="stat-item">
                        <span>Токены:</span>
                        <span class="neon-text" id="tokenCount">0</span>
                    </div>
                    <div class="stat-item">
                        <span>Подписка:</span>
                        <span class="neon-text" id="subscriptionType">Free</span>
                    </div>
                    <div class="stat-item">
                        <span>Запросов сегодня:</span>
                        <span class="neon-text" id="requestsToday">0/34</span>
                    </div>
                    <div class="stat-item">
                        <span>Токенов до Pro:</span>
                        <span class="neon-text" id="tokensToPro">1000</span>
                    </div>
                </div>
                
                <button onclick="showUpgradeModal()" style="width: 100%; margin-bottom: 15px;">
                    💎 Апгрейд до Pro
                </button>
                <button onclick="showAdminModal()" style="width: 100%; background: linear-gradient(45deg, #5500ff, #8800ff);">
                    🔧 Админ-панель
                </button>
                <button onclick="logout()" style="width: 100%; margin-top: 15px; background: linear-gradient(45deg, #ff5500, #ff8800);">
                    🚪 Выйти
                </button>
            </div>
        </div>
        
        <footer>
            <p>© 2024 Mateus AI. Все права защищены.</p>
            <p style="margin-top: 10px; font-size: 0.9em; color: #444;">
                AI анализирует информацию из открытых источников интернета
            </p>
        </footer>
    </div>
    
    <!-- Модальное окно регистрации -->
    <div class="modal" id="loginModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('loginModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 30px;">🔐 Вход / Регистрация</h2>
            
            <div class="form-group">
                <label>Имя пользователя</label>
                <input type="text" id="loginUsername" placeholder="Введите имя">
            </div>
            
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="loginEmail" placeholder="email@example.com">
            </div>
            
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="loginPassword" placeholder="Введите пароль">
            </div>
            
            <div class="error" id="loginError"></div>
            
            <button onclick="registerUser()" style="width: 100%; margin-top: 20px;">
                Зарегистрироваться / Войти
            </button>
        </div>
    </div>
    
    <!-- Модальное окно админа -->
    <div class="modal" id="adminModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('adminModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 30px;">🔧 Админ-панель</h2>
            
            <div class="form-group">
                <label>Пароль администратора</label>
                <input type="password" id="adminPassword" placeholder="Введите пароль админа">
            </div>
            
            <div class="form-group">
                <label>Имя пользователя</label>
                <input type="text" id="adminUsername" placeholder="Для кого изменяем">
            </div>
            
            <div class="form-group">
                <label>Действие</label>
                <select id="adminAction" style="width: 100%; padding: 12px; background: var(--black); color: white; border: 1px solid #444; border-radius: 8px;">
                    <option value="add_tokens">Добавить токены</option>
                    <option value="set_pro">Установить подписку Pro</option>
                    <option value="remove_pro">Убрать подписку Pro</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Количество (для токенов)</label>
                <input type="number" id="adminAmount" placeholder="Количество" value="100">
            </div>
            
            <div class="error" id="adminError"></div>
            
            <button onclick="adminAction()" style="width: 100%; margin-top: 20px;">
                Выполнить действие
            </button>
        </div>
    </div>
    
    <!-- Модальное окно апгрейда -->
    <div class="modal" id="upgradeModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('upgradeModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 30px;">💎 Подписка Pro</h2>
            
            <div style="background: var(--black); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                <h3 style="color: var(--neon-green); margin-bottom: 15px;">Преимущества Pro:</h3>
                <ul style="padding-left: 20px; color: #aaa;">
                    <li>Неограниченное количество запросов в день</li>
                    <li>Приоритетная обработка запросов</li>
                    <li>Расширенный анализ информации</li>
                    <li>Доступ к экспериментальным функциям</li>
                </ul>
            </div>
            
            <div style="text-align: center; padding: 20px; border: 2px solid var(--neon-green); border-radius: 15px; margin-bottom: 20px;">
                <h3>Стоимость: 1000 токенов</h3>
                <p style="color: #aaa; margin-top: 10px;">Накопите токены, используя бесплатную версию</p>
            </div>
            
            <button onclick="upgradeToPro()" style="width: 100%;">
                💰 Активировать Pro за 1000 токенов
            </button>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        // Проверка авторизации при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            checkAuth();
        });
        
        // Функции модальных окон
        function showLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
        }
        
        function showAdminModal() {
            if (!currentUser) {
                showLoginModal();
                return;
            }
            document.getElementById('adminModal').style.display = 'block';
        }
        
        function showUpgradeModal() {
            if (!currentUser) {
                showLoginModal();
                return;
            }
            document.getElementById('upgradeModal').style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Регистрация/авторизация
        async function registerUser() {
            const username = document.getElementById('loginUsername').value;
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            
            if (!username || !email || !password) {
                showError('loginError', 'Заполните все поля');
                return;
            }
            
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, email, password})
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentUser = data.user;
                updateUserInfo();
                closeModal('loginModal');
                addMessage('🤖 Добро пожаловать, ' + username + '! Теперь вы можете задавать вопросы.', 'ai');
            } else {
                showError('loginError', data.error);
            }
        }
        
        // Отправка сообщения
        async function sendMessage() {
            if (!currentUser) {
                showLoginModal();
                return;
            }
            
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Добавляем сообщение пользователя
            addMessage(message, 'user');
            input.value = '';
            
            // Показываем загрузку
            document.getElementById('loader').style.display = 'block';
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: message})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.answer, 'ai');
                    updateUserInfo();
                } else {
                    addMessage('❌ Ошибка: ' + data.error, 'ai');
                }
            } catch (error) {
                addMessage('❌ Ошибка соединения', 'ai');
            }
            
            document.getElementById('loader').style.display = 'none';
        }
        
        // Админ действия
        async function adminAction() {
            const password = document.getElementById('adminPassword').value;
            const username = document.getElementById('adminUsername').value;
            const action = document.getElementById('adminAction').value;
            const amount = document.getElementById('adminAmount').value;
            
            const response = await fetch('/api/admin', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    admin_password: password,
                    username: username,
                    action: action,
                    amount: parseInt(amount)
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('✅ Действие выполнено успешно');
                closeModal('adminModal');
                if (currentUser.username === username) {
                    checkAuth();
                }
            } else {
                showError('adminError', data.error);
            }
        }
        
        // Апгрейд до Pro
        async function upgradeToPro() {
            const response = await fetch('/api/upgrade', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('🎉 Поздравляем! Теперь у вас подписка Pro!');
                currentUser = data.user;
                updateUserInfo();
                closeModal('upgradeModal');
            } else {
                alert('❌ ' + data.error);
            }
        }
        
        // Выход
        async function logout() {
            await fetch('/api/logout');
            currentUser = null;
            updateUserInfo();
            document.getElementById('chatMessages').innerHTML = 
                '<div class="message ai-message">🤖 Вы вышли из системы. Войдите, чтобы продолжить.</div>';
        }
        
        // Вспомогательные функции
        function addMessage(text, sender) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = text.replace(/\n/g, '<br>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function showError(elementId, message) {
            const element = document.getElementById(elementId);
            element.textContent = message;
            element.style.display = 'block';
        }
        
        function updateUserInfo() {
            const userInfoDiv = document.getElementById('userInfo');
            const tokenCount = document.getElementById('tokenCount');
            const subscriptionType = document.getElementById('subscriptionType');
            const requestsToday = document.getElementById('requestsToday');
            const tokensToPro = document.getElementById('tokensToPro');
            
            if (currentUser) {
                userInfoDiv.innerHTML = `
                    👤 ${currentUser.username}<br>
                    <small>${currentUser.subscription === 'pro' ? '💎 Pro' : '🆓 Free'}</small>
                `;
                
                tokenCount.textContent = currentUser.tokens;
                subscriptionType.textContent = currentUser.subscription === 'pro' ? 'Pro' : 'Free';
                requestsToday.textContent = `${currentUser.daily_requests || 0}/${currentUser.subscription === 'pro' ? '∞' : '34'}`;
                
                const needed = 1000 - currentUser.tokens;
                tokensToPro.textContent = needed > 0 ? needed : 'Готово!';
                
                // Скрываем кнопки для Pro пользователей
                document.querySelectorAll('button[onclick="showUpgradeModal()"]').forEach(btn => {
                    btn.style.display = currentUser.subscription === 'pro' ? 'none' : 'block';
                });
            } else {
                userInfoDiv.innerHTML = '<button onclick="showLoginModal()">Войти</button>';
                tokenCount.textContent = '0';
                subscriptionType.textContent = 'None';
                requestsToday.textContent = '0/0';
                tokensToPro.textContent = '1000';
            }
        }
        
        async function checkAuth() {
            try {
                const response = await fetch('/api/me');
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUserInfo();
                }
            } catch (error) {
                console.log('Не авторизован');
            }
        }
        
        // Enter для отправки
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Показываем окно логина при первом заходе
        setTimeout(() => {
            if (!currentUser) {
                showLoginModal();
            }
        }, 1000);
    </script>
</body>
</html>
'''

# API маршруты
@app.route('/')
def index():
    return MAIN_PAGE

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'Все поля обязательны'})
    
    # Проверяем существование пользователя
    user = User.query.filter((User.username == username) | (User.email == email)).first()
    
    if user:
        # Авторизация
        if user.check_password(password):
            session['user_id'] = user.id
            session.permanent = True
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'tokens': user.tokens,
                    'subscription': user.subscription,
                    'daily_requests': user.daily_requests
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Неверный пароль'})
    else:
        # Регистрация
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session.permanent = True
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'tokens': user.tokens,
                'subscription': user.subscription,
                'daily_requests': user.daily_requests
            }
        })

@app.route('/api/me')
def api_me():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'tokens': user.tokens,
                    'subscription': user.subscription,
                    'daily_requests': user.daily_requests
                }
            })
    return jsonify({'success': False})

@app.route('/api/ask', methods=['POST'])
@login_required
def api_ask():
    user = User.query.get(session['user_id'])
    
    # Проверяем лимит
    if not check_daily_limit(user):
        return jsonify({
            'success': False,
            'error': f'Достигнут дневной лимит ({34 if user.subscription == "free" else "∞"} запросов). Завтра снова будет доступно.'
        })
    
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'success': False, 'error': 'Вопрос не может быть пустым'})
    
    # Обрабатываем запрос через ИИ
    response = ai.process_query(question)
    
    # Начисляем токены
    if user.subscription == 'free':
        user.tokens += 10  # 10 токенов за запрос
        db.session.commit()
    
    return jsonify({
        'success': True,
        'answer': response['answer'],
        'sources': response['sources'],
        'confidence': response['confidence']
    })

@app.route('/api/admin', methods=['POST'])
def api_admin():
    data = request.json
    admin_password = data.get('admin_password')
    username = data.get('username')
    action = data.get('action')
    amount = data.get('amount', 100)
    
    # Проверяем пароль админа
    admin_settings = AdminSettings.query.first()
    if not admin_settings or not check_password_hash(admin_settings.admin_password, admin_password):
        return jsonify({'success': False, 'error': 'Неверный пароль администратора'})
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'})
    
    # Выполняем действие
    if action == 'add_tokens':
        user.tokens += amount
        message = f'Добавлено {amount} токенов пользователю {username}'
    elif action == 'set_pro':
        user.subscription = 'pro'
        message = f'Пользователю {username} выдана подписка Pro'
    elif action == 'remove_pro':
        user.subscription = 'free'
        message = f'У пользователя {username} удалена подписка Pro'
    else:
        return jsonify({'success': False, 'error': 'Неизвестное действие'})
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': message})

@app.route('/api/upgrade', methods=['POST'])
@login_required
def api_upgrade():
    user = User.query.get(session['user_id'])
    
    if user.subscription == 'pro':
        return jsonify({'success': False, 'error': 'У вас уже есть подписка Pro'})
    
    if user.tokens < 1000:
        return jsonify({'success': False, 'error': f'Недостаточно токенов. Нужно 1000, у вас {user.tokens}'})
    
    user.tokens -= 1000
    user.subscription = 'pro'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'tokens': user.tokens,
            'subscription': user.subscription
        }
    })

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
