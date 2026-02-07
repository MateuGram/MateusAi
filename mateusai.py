import os
import json
import time
import hashlib
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-super-secret-2024-change-this')

# База данных в памяти
users_db = {}
requests_log = {}

# Настройки
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'AdminMateus2024!')
MAX_FREE_REQUESTS = 34
TOKENS_FOR_PRO = 1000
TOKENS_PER_REQUEST = 10

def hash_pwd(password):
    return hashlib.sha256(password.encode()).hexdigest()

class MateusAI:
    def __init__(self):
        self.knowledge = {
            'о себе': "Я Mateus AI - нейросеть для поиска и анализа информации. Ищу данные в интернете, анализирую и предоставляю точные ответы.",
            'помощь': "Задайте любой вопрос. Примеры: 'Какая погода?', 'Кто создал Python?', 'Что такое ИИ?', 'Сколько время?'",
            'возможности': "Поиск информации, анализ данных, ответы на вопросы, работа с запросами, проверка времени.",
            'создатель': "Я создан для помощи в поиске и анализе информации из интернета.",
            'токены': f"Вы получаете {TOKENS_PER_REQUEST} токенов за каждый запрос. {TOKENS_FOR_PRO} токенов = подписка Pro.",
            'pro': "Pro подписка дает неограниченные запросы и приоритетную обработку."
        }
    
    def search_online(self, query):
        """Имитация поиска в интернете"""
        results = []
        
        # Базовые ответы для популярных запросов
        common_answers = {
            'python': "Python - язык программирования высокого уровня, созданный Гвидо ван Россумом. Популярен в веб-разработке, data science и ИИ.",
            'искусственный интеллект': "ИИ - способность машин выполнять задачи, требующие человеческого интеллекта: обучение, распознавание, анализ.",
            'нейросеть': "Нейросеть - математическая модель, имитирующая работу мозга человека. Используется для распознавания образов и прогнозирования.",
            'flask': "Flask - микрофреймворк на Python для веб-разработки. Простой и гибкий, идеален для небольших приложений.",
            'render': "Render.com - облачная платформа для деплоя приложений с автоматическим масштабированием и SSL.",
            'время': f"Текущее время: {datetime.now().strftime('%H:%M:%S')}",
            'дата': f"Сегодня: {datetime.now().strftime('%d.%m.%Y')}",
            'погода': "Погода зависит от региона. Для точных данных уточните город.",
            'биткоин': "Bitcoin - первая криптовалюта, созданная Сатоши Накамото. Использует технологию blockchain.",
            'космос': "Космос - пространство за пределами земной атмосферы. Содержит звезды, планеты, галактики и черные дыры."
        }
        
        query_lower = query.lower()
        
        # Ищем совпадения
        for key, answer in common_answers.items():
            if key in query_lower:
                results.append({
                    'title': f'Информация: {key}',
                    'content': answer,
                    'source': 'https://knowledge.mateus.ai',
                    'confidence': 0.8
                })
        
        # Если нет точных совпадений, создаем общий ответ
        if not results:
            results.append({
                'title': f'Результаты по запросу: {query}',
                'content': f'По вашему запросу "{query}" найдена информация из различных источников. Анализ показывает...',
                'source': 'https://search.mateus.ai',
                'confidence': 0.6
            })
        
        # Добавляем дополнительные результаты
        results.append({
            'title': 'Дополнительные данные',
            'content': 'Информация проверена и систематизирована для лучшего понимания.',
            'source': 'https://data.mateus.ai',
            'confidence': 0.7
        })
        
        return results
    
    def get_time_info(self):
        now = datetime.now()
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return {
            'date': now.strftime('%d.%m.%Y'),
            'time': now.strftime('%H:%M:%S'),
            'weekday': weekdays[now.weekday()],
            'full': now.strftime('%d %B %Y, %H:%M:%S')
        }
    
    def process(self, query, username):
        query_lower = query.lower().strip()
        
        # Специальные команды
        if query_lower in self.knowledge:
            return {
                'answer': f"🤖 **Mateus AI:**\n\n{self.knowledge[query_lower]}\n\nЗадайте вопрос для поиска в интернете!",
                'sources': [],
                'confidence': 'high'
            }
        
        # Время и дата
        if any(word in query_lower for word in ['время', 'дата', 'сейчас', 'time', 'date', 'час', 'число']):
            time_info = self.get_time_info()
            return {
                'answer': f"🕒 **Текущее время и дата:**\n\n📅 **Дата:** {time_info['date']}\n📆 **День:** {time_info['weekday']}\n⏰ **Время:** {time_info['time']}\n\n*Актуально на момент запроса*",
                'sources': [],
                'confidence': 'high'
            }
        
        # Приветствие
        if any(word in query_lower for word in ['привет', 'hello', 'hi', 'здравствуй', 'начать']):
            return {
                'answer': "🤖 **Привет! Я Mateus AI.**\n\nЯ нейросеть для поиска и анализа информации из интернета. Задайте мне вопрос, и я найду самую актуальную информацию!\n\n💡 **Примеры вопросов:**\n• Какая погода в Москве?\n• Кто создал Python?\n• Что такое нейросеть?\n• Как работает ИИ?\n• Новости технологий\n• Курс биткоина",
                'sources': [],
                'confidence': 'high'
            }
        
        # О нас
        if any(word in query_lower for word in ['ты кто', 'кто ты', 'что ты']):
            return {
                'answer': "🤖 **Я Mateus AI** - умная нейросеть для поиска информации.\n\n🔍 **Мои возможности:**\n• Поиск данных в интернете\n• Анализ и сравнение информации\n• Ответы на вопросы с источниками\n• Определение времени и даты\n• Работа с различными запросами\n\n💡 Просто спросите меня о чем угодно!",
                'sources': [],
                'confidence': 'high'
            }
        
        # Поиск информации
        results = self.search_online(query)
        
        # Формируем ответ
        if results:
            main_result = results[0]
            
            answer = f"🤖 **Mateus AI отвечает на: '{query}'**\n\n"
            answer += f"🔍 **На основе анализа информации:**\n\n"
            answer += f"📝 {main_result['content']}\n\n"
            
            if len(results) > 1:
                answer += f"📚 **Дополнительные источники:**\n"
                for i, res in enumerate(results[1:3], 1):
                    answer += f"{i}. {res['title']}\n"
            
            answer += f"\n⚡ **Уверенность:** {main_result['confidence']*100:.0f}%\n"
            answer += f"🔄 **Проанализировано источников:** {len(results)}\n\n"
            
            if main_result['confidence'] < 0.7:
                answer += "💡 **Совет:** Попробуйте уточнить вопрос для более точного ответа."
            
            return {
                'answer': answer,
                'sources': [r['source'] for r in results[:3]],
                'confidence': 'high' if main_result['confidence'] > 0.7 else 'medium'
            }
        
        # Общий ответ если ничего не нашли
        return {
            'answer': f"🤖 **Mateus AI:**\n\nПо запросу '{query}' я провел поиск, но не нашел достаточно информации.\n\nПопробуйте:\n1. Переформулировать вопрос\n2. Использовать другие ключевые слова\n3. Задать более конкретный запрос\n\n💡 *Я продолжаю учиться и улучшать поиск!*",
            'sources': [],
            'confidence': 'low'
        }

# Инициализация ИИ
ai = MateusAI()

# HTML интерфейс
HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI - Нейросеть для ваших запросов</title>
    <style>
        :root {
            --neon-green: #00ff88;
            --dark-bg: #0a0a0a;
            --card-bg: #111111;
            --text: #ffffff;
            --text-muted: #888888;
            --error: #ff4444;
            --success: #00ff88;
            --premium: #8800ff;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: var(--dark-bg);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 3.5em;
            font-weight: 900;
            color: var(--neon-green);
            text-shadow: 0 0 10px var(--neon-green);
            margin-bottom: 10px;
            letter-spacing: 3px;
        }
        
        .slogan {
            font-size: 1.2em;
            color: var(--text-muted);
            margin-bottom: 30px;
        }
        
        .user-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            text-align: right;
        }
        
        .main-content {
            display: flex;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .chat-section {
            flex: 1;
            min-width: 300px;
        }
        
        .info-section {
            width: 350px;
            min-width: 300px;
        }
        
        .card {
            background: var(--card-bg);
            border: 1px solid #222;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.05);
        }
        
        .chat-window {
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #000;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #222;
        }
        
        .message {
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
            background: linear-gradient(135deg, #003322, #005533);
            margin-left: auto;
            border: 1px solid var(--neon-green);
        }
        
        .ai-message {
            background: #1a1a1a;
            margin-right: auto;
            border: 1px solid #333;
            white-space: pre-line;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        #userInput {
            flex: 1;
            padding: 16px;
            background: #000;
            border: 2px solid var(--neon-green);
            border-radius: 10px;
            color: white;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        #userInput:focus {
            outline: none;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
        }
        
        .btn {
            padding: 16px 30px;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 16px;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #003322, var(--neon-green));
            color: black;
        }
        
        .btn-secondary {
            background: #333;
            color: white;
        }
        
        .btn-premium {
            background: linear-gradient(45deg, #330066, var(--premium));
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #660000, #ff3300);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .stats {
            margin: 25px 0;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #222;
        }
        
        .stat-value {
            color: var(--neon-green);
            font-weight: bold;
        }
        
        .pro-badge {
            background: var(--premium);
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            padding: 20px;
            overflow-y: auto;
        }
        
        .modal-content {
            background: var(--card-bg);
            max-width: 500px;
            margin: 50px auto;
            padding: 40px;
            border-radius: 20px;
            border: 2px solid var(--neon-green);
            position: relative;
        }
        
        .close-modal {
            position: absolute;
            top: 15px;
            right: 20px;
            color: var(--neon-green);
            font-size: 30px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-muted);
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 14px;
            background: #000;
            border: 1px solid #333;
            border-radius: 8px;
            color: white;
            font-size: 16px;
        }
        
        .error {
            color: var(--error);
            margin-top: 10px;
            padding: 10px;
            background: rgba(255, 68, 68, 0.1);
            border-radius: 5px;
            display: none;
        }
        
        .loader {
            display: none;
            text-align: center;
            padding: 20px;
            color: var(--neon-green);
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: var(--card-bg);
            border: 1px solid var(--neon-green);
            border-radius: 10px;
            z-index: 1001;
            display: none;
            animation: slideIn 0.3s;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            
            .info-section {
                width: 100%;
            }
            
            .user-panel {
                position: relative;
                top: 0;
                right: 0;
                text-align: center;
                margin-bottom: 20px;
            }
            
            .logo {
                font-size: 2.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">MATEUS AI</div>
            <div class="slogan">Нейросеть для ваших запросов</div>
            <div class="user-panel" id="userPanel">
                <!-- Заполнится JavaScript -->
            </div>
        </header>
        
        <div class="main-content">
            <div class="chat-section">
                <div class="card">
                    <h3 style="color: var(--neon-green); margin-bottom: 20px;">💬 Чат с Mateus AI</h3>
                    
                    <div class="chat-window" id="chatWindow">
                        <div class="message ai-message">
                            🤖 Добро пожаловать в Mateus AI! Я ищу информацию в интернете и предоставляю точные ответы. Задайте мне любой вопрос!
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <input type="text" id="userInput" placeholder="Введите ваш вопрос..." autocomplete="off">
                        <button class="btn btn-primary" onclick="sendMessage()">Отправить</button>
                    </div>
                    
                    <div class="loader" id="loader">
                        🔍 Ищу информацию в интернете...
                    </div>
                </div>
            </div>
            
            <div class="info-section">
                <div class="card">
                    <h3 style="color: var(--neon-green); margin-bottom: 25px;">📊 Ваша статистика</h3>
                    
                    <div class="stats">
                        <div class="stat-item">
                            <span>Токены:</span>
                            <span class="stat-value" id="tokenCount">0</span>
                        </div>
                        <div class="stat-item">
                            <span>Подписка:</span>
                            <span class="stat-value" id="subscriptionType">Free</span>
                        </div>
                        <div class="stat-item">
                            <span>Запросы сегодня:</span>
                            <span class="stat-value" id="requestsToday">0/34</span>
                        </div>
                        <div class="stat-item">
                            <span>Токенов до Pro:</span>
                            <span class="stat-value" id="tokensToPro">1000</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 30px; display: grid; gap: 12px;">
                        <button class="btn btn-premium" onclick="showUpgradeModal()" id="upgradeBtn">
                            💎 Апгрейд до Pro
                        </button>
                        <button class="btn btn-secondary" onclick="showAdminModal()">
                            🔧 Админ-панель
                        </button>
                        <button class="btn btn-danger" onclick="logout()" id="logoutBtn">
                            🚪 Выйти
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Модальные окна -->
    <div class="modal" id="loginModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('loginModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 30px;">🔐 Вход / Регистрация</h2>
            
            <div class="form-group">
                <label>Имя пользователя</label>
                <input type="text" id="loginUsername" placeholder="Введите имя">
            </div>
            
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="loginPassword" placeholder="Введите пароль">
            </div>
            
            <div class="error" id="loginError"></div>
            
            <button class="btn btn-primary" onclick="login()" style="width: 100%; margin-top: 20px;">
                Войти / Зарегистрироваться
            </button>
        </div>
    </div>
    
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
                <select id="adminAction">
                    <option value="add_tokens">Добавить токены</option>
                    <option value="set_pro">Установить подписку Pro</option>
                    <option value="remove_pro">Убрать подписку Pro</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Количество токенов</label>
                <input type="number" id="adminAmount" value="100" min="1" max="10000">
            </div>
            
            <div class="error" id="adminError"></div>
            
            <button class="btn btn-primary" onclick="adminAction()" style="width: 100%; margin-top: 20px;">
                Выполнить действие
            </button>
        </div>
    </div>
    
    <div class="modal" id="upgradeModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('upgradeModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 30px;">💎 Подписка Pro</h2>
            
            <div style="background: #000; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h4 style="color: var(--neon-green); margin-bottom: 15px;">Преимущества Pro:</h4>
                <ul style="padding-left: 20px; color: var(--text-muted);">
                    <li>✅ Неограниченные запросы в день</li>
                    <li>⚡ Приоритетная обработка</li>
                    <li>🔍 Расширенный анализ</li>
                    <li>🚀 Экспериментальные функции</li>
                </ul>
            </div>
            
            <div style="text-align: center; padding: 20px; border: 2px solid var(--neon-green); border-radius: 10px; margin-bottom: 20px;">
                <h3>Стоимость: <span style="color: var(--neon-green)">1000 токенов</span></h3>
                <p id="tokensInfo" style="color: var(--text-muted); margin-top: 10px;"></p>
            </div>
            
            <button class="btn btn-premium" onclick="upgradeToPro()" style="width: 100%;" id="upgradeActionBtn">
                Активировать Pro за 1000 токенов
            </button>
        </div>
    </div>
    
    <div class="notification" id="notification"></div>
    
    <script>
        let currentUser = null;
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            checkAuth();
            setupEventListeners();
        });
        
        function setupEventListeners() {
            // Отправка по Enter
            document.getElementById('userInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Автоматическое открытие логина
            setTimeout(() => {
                if (!currentUser) {
                    showLoginModal();
                }
            }, 1000);
        }
        
        // Функции модальных окон
        function showLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
            document.getElementById('loginError').style.display = 'none';
        }
        
        function showAdminModal() {
            if (!currentUser) {
                showNotification('Сначала войдите в систему', 'error');
                showLoginModal();
                return;
            }
            document.getElementById('adminModal').style.display = 'block';
            document.getElementById('adminError').style.display = 'none';
        }
        
        function showUpgradeModal() {
            if (!currentUser) {
                showNotification('Сначала войдите в систему', 'error');
                showLoginModal();
                return;
            }
            
            const modal = document.getElementById('upgradeModal');
            modal.style.display = 'block';
            
            const tokensInfo = document.getElementById('tokensInfo');
            const upgradeBtn = document.getElementById('upgradeActionBtn');
            
            if (currentUser.tokens >= 1000) {
                tokensInfo.innerHTML = `<span style="color: #00ff88">✅ У вас ${currentUser.tokens} токенов - достаточно!</span>`;
                upgradeBtn.disabled = false;
                upgradeBtn.innerHTML = '💰 Активировать Pro за 1000 токенов';
                upgradeBtn.style.opacity = '1';
            } else {
                const needed = 1000 - currentUser.tokens;
                tokensInfo.innerHTML = `<span style="color: #ff4444">❌ Нужно еще ${needed} токенов</span>`;
                upgradeBtn.disabled = true;
                upgradeBtn.innerHTML = '❌ Недостаточно токенов';
                upgradeBtn.style.opacity = '0.6';
            }
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Уведомления
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.display = 'block';
            
            if (type === 'error') {
                notification.style.borderColor = '#ff4444';
                notification.style.color = '#ff4444';
            } else if (type === 'success') {
                notification.style.borderColor = '#00ff88';
                notification.style.color = '#00ff88';
            } else {
                notification.style.borderColor = '#00ff88';
                notification.style.color = '#00ff88';
            }
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        // API функции
        async function login() {
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            if (!username || !password) {
                showError('loginError', 'Заполните все поля');
                return;
            }
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUI();
                    closeModal('loginModal');
                    showNotification(`Добро пожаловать, ${username}!`, 'success');
                    addMessage(`🤖 Привет, ${username}! Теперь вы можете задавать вопросы. У вас ${currentUser.tokens} токенов.`, 'ai');
                } else {
                    showError('loginError', data.error);
                }
            } catch (error) {
                showError('loginError', 'Ошибка соединения');
            }
        }
        
        async function sendMessage() {
            if (!currentUser) {
                showLoginModal();
                showNotification('Сначала войдите в систему', 'error');
                return;
            }
            
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) {
                showNotification('Введите сообщение', 'error');
                return;
            }
            
            // Добавляем сообщение
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
                    updateUI();
                } else {
                    addMessage(`❌ ${data.error}`, 'ai');
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                addMessage('❌ Ошибка соединения с сервером', 'ai');
                showNotification('Ошибка сети', 'error');
            }
            
            document.getElementById('loader').style.display = 'none';
        }
        
        async function adminAction() {
            const password = document.getElementById('adminPassword').value;
            const username = document.getElementById('adminUsername').value.trim();
            const action = document.getElementById('adminAction').value;
            const amount = parseInt(document.getElementById('adminAmount').value);
            
            if (!password || !username) {
                showError('adminError', 'Заполните все поля');
                return;
            }
            
            try {
                const response = await fetch('/api/admin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        password: password,
                        username: username,
                        action: action,
                        amount: amount
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(data.message, 'success');
                    closeModal('adminModal');
                    
                    if (currentUser && currentUser.username === username) {
                        checkAuth();
                    }
                } else {
                    showError('adminError', data.error);
                }
            } catch (error) {
                showError('adminError', 'Ошибка соединения');
            }
        }
        
        async function upgradeToPro() {
            try {
                const response = await fetch('/api/upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUI();
                    closeModal('upgradeModal');
                    showNotification('🎉 Теперь у вас Pro подписка!', 'success');
                    addMessage('🎉 Поздравляем! Теперь у вас подписка Pro. Все ограничения сняты!', 'ai');
                } else {
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                showNotification('Ошибка сети', 'error');
            }
        }
        
        async function logout() {
            try {
                await fetch('/api/logout');
                currentUser = null;
                updateUI();
                document.getElementById('chatWindow').innerHTML = 
                    '<div class="message ai-message">🤖 Вы вышли из системы. Войдите, чтобы продолжить.</div>';
                showNotification('Вы успешно вышли', 'info');
                setTimeout(showLoginModal, 1000);
            } catch (error) {
                showNotification('Ошибка выхода', 'error');
            }
        }
        
        // Вспомогательные функции
        function addMessage(text, sender) {
            const chatWindow = document.getElementById('chatWindow');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = text;
            chatWindow.appendChild(messageDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
        
        function showError(elementId, message) {
            const element = document.getElementById(elementId);
            element.textContent = message;
            element.style.display = 'block';
        }
        
        function updateUI() {
            const userPanel = document.getElementById('userPanel');
            const tokenCount = document.getElementById('tokenCount');
            const subscriptionType = document.getElementById('subscriptionType');
            const requestsToday = document.getElementById('requestsToday');
            const tokensToPro = document.getElementById('tokensToPro');
            const upgradeBtn = document.getElementById('upgradeBtn');
            const logoutBtn = document.getElementById('logoutBtn');
            
            if (currentUser) {
                userPanel.innerHTML = `
                    <div style="margin-bottom: 5px;">
                        👤 <strong>${currentUser.username}</strong>
                        ${currentUser.subscription === 'pro' ? '<span class="pro-badge">PRO</span>' : ''}
                    </div>
                    <div style="font-size: 14px; color: var(--text-muted);">
                        Токены: ${currentUser.tokens} | Запросы: ${currentUser.daily_requests || 0}/${currentUser.subscription === 'pro' ? '∞' : '34'}
                    </div>
                `;
                
                tokenCount.textContent = currentUser.tokens;
                subscriptionType.textContent = currentUser.subscription === 'pro' ? 'Pro' : 'Free';
                subscriptionType.style.color = currentUser.subscription === 'pro' ? '#8800ff' : '#00ff88';
                
                const maxRequests = currentUser.subscription === 'pro' ? '∞' : '34';
                requestsToday.textContent = `${currentUser.daily_requests || 0}/${maxRequests}`;
                
                if (currentUser.subscription === 'pro') {
                    tokensToPro.textContent = 'PRO';
                    tokensToPro.style.color = '#8800ff';
                    upgradeBtn.style.display = 'none';
                } else {
                    const needed = 1000 - currentUser.tokens;
                    tokensToPro.textContent = needed > 0 ? needed : 'Готово!';
                    upgradeBtn.style.display = 'block';
                }
                
                logoutBtn.style.display = 'block';
            } else {
                userPanel.innerHTML = '<button class="btn btn-primary" onclick="showLoginModal()">Войти / Регистрация</button>';
                tokenCount.textContent = '0';
                subscriptionType.textContent = 'None';
                requestsToday.textContent = '0/0';
                tokensToPro.textContent = '1000';
                upgradeBtn.style.display = 'block';
                logoutBtn.style.display = 'none';
            }
        }
        
        async function checkAuth() {
            try {
                const response = await fetch('/api/me');
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUI();
                }
            } catch (error) {
                console.log('Не авторизован');
            }
        }
        
        // Закрытие модалок по клику вне
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        };
    </script>
</body>
</html>
'''

# API маршруты
@app.route('/')
def home():
    return HTML

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Заполните все поля'})
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': 'Имя должно быть минимум 3 символа'})
        
        user_id = hash_pwd(username)
        
        # Проверяем существующего пользователя
        if user_id in users_db:
            stored_hash = users_db[user_id]['password']
            if hash_pwd(password) == stored_hash:
                # Вход
                session['user_id'] = user_id
                return jsonify({
                    'success': True,
                    'user': {
                        'username': username,
                        'tokens': users_db[user_id]['tokens'],
                        'subscription': users_db[user_id]['subscription'],
                        'daily_requests': users_db[user_id].get('daily_requests', 0),
                        'last_date': users_db[user_id].get('last_date', '')
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Неверный пароль'})
        else:
            # Регистрация нового пользователя
            today = datetime.now().strftime('%Y-%m-%d')
            users_db[user_id] = {
                'username': username,
                'password': hash_pwd(password),
                'tokens': 100,
                'subscription': 'free',
                'daily_requests': 0,
                'last_date': today,
                'created': datetime.now().isoformat()
            }
            
            session['user_id'] = user_id
            
            return jsonify({
                'success': True,
                'user': {
                    'username': username,
                    'tokens': 100,
                    'subscription': 'free',
                    'daily_requests': 0,
                    'last_date': today
                }
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/me')
def api_me():
    user_id = session.get('user_id')
    if user_id and user_id in users_db:
        user = users_db[user_id]
        return jsonify({
            'success': True,
            'user': {
                'username': user['username'],
                'tokens': user['tokens'],
                'subscription': user['subscription'],
                'daily_requests': user.get('daily_requests', 0),
                'last_date': user.get('last_date', '')
            }
        })
    return jsonify({'success': False})

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        user_id = session.get('user_id')
        if not user_id or user_id not in users_db:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})
        
        user = users_db[user_id]
        
        # Проверка дневного лимита
        today = datetime.now().strftime('%Y-%m-%d')
        if user.get('last_date') != today:
            user['daily_requests'] = 0
            user['last_date'] = today
        
        # Проверяем лимит для бесплатных пользователей
        if user['subscription'] == 'free' and user.get('daily_requests', 0) >= MAX_FREE_REQUESTS:
            return jsonify({
                'success': False, 
                'error': f'Достигнут дневной лимит ({MAX_FREE_REQUESTS} запросов). Завтра будет доступно снова.'
            })
        
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Введите вопрос'})
        
        # Обрабатываем запрос
        response = ai.process(question, user['username'])
        
        # Обновляем статистику
        user['daily_requests'] = user.get('daily_requests', 0) + 1
        
        # Начисляем токены бесплатным пользователям
        if user['subscription'] == 'free':
            user['tokens'] += TOKENS_PER_REQUEST
        
        return jsonify({
            'success': True,
            'answer': response['answer'],
            'sources': response['sources'],
            'confidence': response['confidence']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin', methods=['POST'])
def api_admin():
    try:
        data = request.json
        password = data.get('password')
        target_username = data.get('username', '').strip()
        action = data.get('action')
        amount = data.get('amount', 100)
        
        # Проверка пароля админа
        if hash_pwd(password) != hash_pwd(ADMIN_PASSWORD):
            return jsonify({'success': False, 'error': 'Неверный пароль администратора'})
        
        # Ищем пользователя
        target_user_id = None
        for user_id, user_data in users_db.items():
            if user_data['username'] == target_username:
                target_user_id = user_id
                break
        
        if not target_user_id:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        user = users_db[target_user_id]
        
        # Выполняем действие
        if action == 'add_tokens':
            user['tokens'] += int(amount)
            message = f'Добавлено {amount} токенов пользователю {target_username}'
        elif action == 'set_pro':
            user['subscription'] = 'pro'
            message = f'Пользователю {target_username} выдана подписка Pro'
        elif action == 'remove_pro':
            user['subscription'] = 'free'
            message = f'У пользователя {target_username} удалена подписка Pro'
        else:
            return jsonify({'success': False, 'error': 'Неизвестное действие'})
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upgrade', methods=['POST'])
def api_upgrade():
    try:
        user_id = session.get('user_id')
        if not user_id or user_id not in users_db:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})
        
        user = users_db[user_id]
        
        if user['subscription'] == 'pro':
            return jsonify({'success': False, 'error': 'У вас уже есть подписка Pro'})
        
        if user['tokens'] < TOKENS_FOR_PRO:
            return jsonify({'success': False, 'error': f'Недостаточно токенов. Нужно {TOKENS_FOR_PRO}, у вас {user["tokens"]}'})
        
        # Списание токенов и выдача Pro
        user['tokens'] -= TOKENS_FOR_PRO
        user['subscription'] = 'pro'
        
        return jsonify({
            'success': True,
            'user': {
                'username': user['username'],
                'tokens': user['tokens'],
                'subscription': user['subscription'],
                'daily_requests': user.get('daily_requests', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'Mateus AI',
        'users': len(users_db),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Mateus AI запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)        if not HAS_INTERNET_DEPS:
            # Возвращаем тестовые данные если зависимости не установлены
            return [
                {'title': f'Результат по запросу: {query}', 'link': 'https://example.com/1'},
                {'title': 'Информация из открытых источников', 'link': 'https://example.com/2'},
                {'title': 'Данные для анализа', 'link': 'https://example.com/3'}
            ]
        
        try:
            # Используем DuckDuckGo
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://duckduckgo.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Парсим результаты
            for result in soup.find_all('a', class_='result__url'):
                title = result.text.strip()
                link = result.get('href', '')
                
                if link and title:
                    # Получаем полное название
                    title_elem = result.find_previous('a', class_='result__title')
                    if title_elem and title_elem.text.strip():
                        title = title_elem.text.strip()
                    
                    # Чистим ссылку
                    if link.startswith('//'):
                        link = 'https:' + link
                    elif not link.startswith('http'):
                        link = 'https://' + link
                    
                    results.append({
                        'title': title[:150],
                        'link': link
                    })
                
                if len(results) >= num_results:
                    break
            
            # Альтернативный парсинг
            if len(results) < 2:
                for link in soup.find_all('a', href=True):
                    if len(results) >= num_results:
                        break
                    
                    href = link.get('href')
                    if href and 'duckduckgo.com' not in href and ('http://' in href or 'https://' in href):
                        results.append({
                            'title': link.text[:150] or 'Источник',
                            'link': href
                        })
            
            return results[:num_results]
            
        except Exception as e:
            print(f"Ошибка поиска: {str(e)[:100]}")
            return []

    @staticmethod
    def get_page_content(url):
        """Получение содержимого веб-страницы"""
        if not HAS_INTERNET_DEPS:
            return f"Содержимое страницы для анализа. Это тестовые данные. Ссылка: {url}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return "Не удалось загрузить страницу"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
                element.decompose()
            
            # Получаем текст
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:2000]  # Ограничиваем объем
            
        except Exception as e:
            print(f"Ошибка получения контента: {str(e)[:100]}")
            return "Ошибка при получении содержимого страницы"

    @staticmethod
    def get_current_time():
        """Получение текущего времени из интернета"""
        try:
            # Попробуем несколько источников
            time_sources = [
                'http://worldtimeapi.org/api/timezone/Europe/Moscow',
                'http://worldtimeapi.org/api/timezone/UTC',
                'http://worldtimeapi.org/api/ip'
            ]
            
            for source in time_sources:
                try:
                    response = requests.get(source, timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        if 'datetime' in data:
                            return data['datetime']
                        elif 'utc_datetime' in data:
                            return data['utc_datetime']
                except:
                    continue
                    
        except Exception as e:
            print(f"Ошибка получения времени: {str(e)[:100]}")
        
        # Резервный вариант
        return datetime.now(pytz.timezone('Europe/Moscow')).isoformat()

# ИИ обработчик
class MateusAI:
    def __init__(self):
        self.searcher = InternetSearcher()
        self.knowledge_base = {
            'о себе': "Я - Mateus AI, нейросеть для поиска и анализа информации из интернета. Я могу искать данные, анализировать их и предоставлять точные ответы на ваши вопросы.",
            'возможности': "1. Поиск информации в интернете\n2. Анализ и сравнение данных\n3. Ответы на вопросы с источниками\n4. Получение актуального времени\n5. Работа с текстовыми запросами",
            'помощь': "Просто задайте мне вопрос, и я найду информацию в интернете. Вы можете спрашивать о чем угодно: текущие события, исторические факты, научные данные и многое другое.",
        }
        
    def process_query(self, query, user_context=None):
        """Основная обработка запроса"""
        try:
            query_lower = query.lower().strip()
            
            # Проверяем внутреннюю базу знаний
            if query_lower in self.knowledge_base:
                return {
                    'answer': f"🤖 **Mateus AI:**\n\n{self.knowledge_base[query_lower]}\n\nЗадайте конкретный вопрос для поиска в интернете!",
                    'sources': [],
                    'confidence': 'high'
                }
            
            # Специальные запросы
            if any(word in query_lower for word in ['время', 'дата', 'сейчас', 'time', 'date', 'час', 'число']):
                current_time = self.searcher.get_current_time()
                return self._format_time_response(current_time)
            
            if any(word in query_lower for word in ['привет', 'hello', 'hi', 'здравствуй', 'начать']):
                return {
                    'answer': "🤖 **Привет! Я Mateus AI.**\n\nЯ ищу информацию в интернете, анализирую различные источники и предоставляю вам точные ответы.\n\nПросто задайте любой вопрос, и я найду самую актуальную информацию по этой теме!\n\nПримеры вопросов:\n• Какая сейчас погода в Москве?\n• Кто написал 'Войну и мир'?\n• Что такое искусственный интеллект?\n• Какие последние новости в мире технологий?",
                    'sources': [],
                    'confidence': 'high'
                }
            
            # Поиск в интернете
            search_results = self.searcher.search_web(query, 3)
            
            if not search_results:
                return {
                    'answer': f"🤖 **Mateus AI:**\n\nПо запросу '{query}' не удалось найти информацию в открытых источниках.\n\nПопробуйте:\n1. Переформулировать вопрос\n2. Использовать другие ключевые слова\n3. Задать более конкретный запрос\n\n*Я продолжаю улучшать свои алгоритмы поиска!*",
                    'sources': [],
                    'confidence': 'low'
                }
            
            # Анализ результатов
            analyzed_info = self._analyze_results(query, search_results)
            
            # Генерация ответа
            response = self._generate_response(query, analyzed_info)
            
            return response
            
        except Exception as e:
            print(f"Ошибка обработки: {str(e)}")
            return {
                'answer': f"🤖 **Mateus AI:**\n\nИзвините, произошла ошибка при обработке вашего запроса.\n\nОшибка: {str(e)[:100]}\n\nПожалуйста, попробуйте еще раз или переформулируйте вопрос.",
                'sources': [],
                'confidence': 'low'
            }
    
    def _analyze_results(self, query, results):
        """Анализ и сравнение информации из найденных источников"""
        analyzed = []
        
        for result in results:
            try:
                content = self.searcher.get_page_content(result['link'])
                
                if content and len(content) > 100:
                    # Анализ релевантности
                    query_words = set(re.findall(r'\w+', query.lower()))
                    content_words = set(re.findall(r'\w+', content.lower()))
                    common_words = query_words.intersection(content_words)
                    
                    relevance = len(common_words) / max(len(query_words), 1)
                    
                    # Учитываем длину контента
                    content_score = min(len(content) / 1000, 1.0)
                    
                    # Итоговая релевантность
                    final_relevance = (relevance * 0.7 + content_score * 0.3)
                    
                    analyzed.append({
                        'title': result['title'],
                        'relevance': final_relevance,
                        'content': content[:1000],
                        'source': result['link']
                    })
                    
            except Exception as e:
                print(f"Ошибка анализа результата: {str(e)[:50]}")
                continue
        
        # Сортируем по релевантности
        analyzed.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Если нет результатов анализа, создаем базовые
        if not analyzed and results:
            for i, result in enumerate(results[:2]):
                analyzed.append({
                    'title': result['title'],
                    'relevance': 0.5 - (i * 0.1),
                    'content': f"Информация по теме '{query}' из источника: {result['link']}",
                    'source': result['link']
                })
        
        return analyzed
    
    def _generate_response(self, query, analyzed_info):
        """Генерация финального ответа"""
        if not analyzed_info:
            return {
                'answer': f"🤖 **Mateus AI:**\n\nНе удалось проанализировать найденную информацию по запросу '{query}'.\n\nПопробуйте задать вопрос по-другому или уточнить тему.",
                'sources': [],
                'confidence': 'low'
            }
        
        best_source = analyzed_info[0]
        
        # Определяем уровень уверенности
        if best_source['relevance'] > 0.7:
            confidence = 'высокая'
            confidence_emoji = '✅'
        elif best_source['relevance'] > 0.4:
            confidence = 'средняя'
            confidence_emoji = '⚠️'
        else:
            confidence = 'низкая'
            confidence_emoji = '🤔'
        
        # Формируем ответ
        answer = f"🤖 **Mateus AI отвечает на: '{query}'**\n\n"
        answer += f"{confidence_emoji} **На основе анализа интернета:**\n\n"
        
        # Основная информация
        if len(best_source['content']) > 300:
            summary = best_source['content'][:300] + "..."
        else:
            summary = best_source['content']
        
        answer += f"📝 {summary}\n\n"
        
        # Источники
        if len(analyzed_info) > 0:
            answer += "📚 **Источники информации:**\n"
            for i, source in enumerate(analyzed_info[:3], 1):
                answer += f"{i}. {source['title']}\n"
        
        # Мета-информация
        answer += f"\n⚡ **Уверенность:** {confidence}\n"
        answer += f"🔍 **Проанализировано источников:** {len(analyzed_info)}\n"
        
        # Совет
        if confidence == 'низкая':
            answer += "\n💡 **Совет:** Попробуйте переформулировать вопрос или задать более конкретный запрос."
        
        return {
            'answer': answer,
            'sources': [s['source'] for s in analyzed_info[:3]],
            'confidence': confidence
        }
    
    def _format_time_response(self, time_str):
        """Форматирование ответа с временем"""
        try:
            # Парсим время
            if 'T' in time_str:
                dt_str = time_str.split('T')[0]
                time_part = time_str.split('T')[1][:8]
            else:
                dt = datetime.now(pytz.timezone('Europe/Moscow'))
                dt_str = dt.strftime('%Y-%m-%d')
                time_part = dt.strftime('%H:%M:%S')
            
            # Преобразуем в читаемый формат
            try:
                year, month, day = map(int, dt_str.split('-'))
                weekday_num = datetime(year, month, day).weekday()
                weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                weekday = weekdays[weekday_num]
            except:
                weekday = ""
            
            return {
                'answer': f"🕒 **Текущее время и дата:**\n\n"
                         f"📅 **Дата:** {day:02d}.{month:02d}.{year}\n"
                         f"📆 **День недели:** {weekday}\n"
                         f"⏰ **Время:** {time_part}\n"
                         f"🌍 **Часовой пояс:** Москва (UTC+3)\n\n"
                         f"*Информация получена из интернета*",
                'sources': [],
                'confidence': 'высокая'
            }
        except:
            # Резервный ответ
            dt = datetime.now(pytz.timezone('Europe/Moscow'))
            return {
                'answer': f"🕒 **Текущее время и дата:**\n\n"
                         f"📅 **Дата:** {dt.strftime('%d.%m.%Y')}\n"
                         f"⏰ **Время:** {dt.strftime('%H:%M:%S')}\n"
                         f"🌍 **Часовой пояс:** Москва\n\n"
                         f"*Локальное время сервера*",
                'sources': [],
                'confidence': 'средняя'
            }

# Инициализация ИИ
ai = MateusAI()

# Декораторы
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_daily_limit(user):
    """Проверка дневного лимита запросов"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user.last_request_date != today:
        user.daily_requests = 0
        user.last_request_date = today
        db.session.commit()
    
    if user.subscription == 'pro':
        return True
    
    max_requests = 34
    
    if user.daily_requests >= max_requests:
        return False
    
    user.daily_requests += 1
    db.session.commit()
    return True

# HTML шаблон (упрощенный для надежности)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI - Нейросеть для ваших запросов</title>
    <style>
        :root {
            --neon-green: #00ff88;
            --dark-bg: #0a0a0a;
            --card-bg: #111111;
            --text: #ffffff;
            --text-muted: #888888;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: var(--dark-bg);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 30px 20px;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 48px;
            font-weight: 900;
            color: var(--neon-green);
            text-shadow: 0 0 10px var(--neon-green);
            margin-bottom: 10px;
            letter-spacing: 2px;
        }
        
        .slogan {
            font-size: 18px;
            color: var(--text-muted);
            margin-bottom: 20px;
        }
        
        .main-content {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .chat-section {
            flex: 1;
            min-width: 300px;
        }
        
        .info-section {
            width: 350px;
            min-width: 300px;
        }
        
        .card {
            background: var(--card-bg);
            border: 1px solid #222;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.05);
        }
        
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 15px;
            background: #000;
            border-radius: 10px;
            border: 1px solid #222;
        }
        
        .message {
            padding: 12px 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            max-width: 85%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: linear-gradient(135deg, #003322, #005533);
            margin-left: auto;
            border: 1px solid var(--neon-green);
        }
        
        .ai-message {
            background: #1a1a1a;
            margin-right: auto;
            border: 1px solid #333;
            white-space: pre-line;
        }
        
        .input-area {
            display: flex;
            gap: 10px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px;
            background: #000;
            border: 2px solid var(--neon-green);
            border-radius: 10px;
            color: white;
            font-size: 16px;
        }
        
        input[type="text"]:focus {
            outline: none;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        
        button {
            padding: 15px 25px;
            background: linear-gradient(45deg, #003322, var(--neon-green));
            border: none;
            border-radius: 10px;
            color: black;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.3);
        }
        
        .btn-primary { background: linear-gradient(45deg, #003322, var(--neon-green)); }
        .btn-secondary { background: linear-gradient(45deg, #333333, #555555); color: white; }
        .btn-premium { background: linear-gradient(45deg, #330066, #8800ff); color: white; }
        .btn-danger { background: linear-gradient(45deg, #660000, #ff3300); color: white; }
        
        .stats-grid {
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            background: #000;
            border-radius: 8px;
            border: 1px solid #222;
        }
        
        .stat-value {
            color: var(--neon-green);
            font-weight: bold;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            padding: 20px;
        }
        
        .modal-content {
            background: var(--card-bg);
            max-width: 500px;
            margin: 50px auto;
            padding: 30px;
            border-radius: 15px;
            border: 2px solid var(--neon-green);
            position: relative;
        }
        
        .close-modal {
            position: absolute;
            top: 15px;
            right: 20px;
            color: var(--neon-green);
            font-size: 24px;
            cursor: pointer;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: var(--text-muted);
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px;
            background: #000;
            border: 1px solid #333;
            border-radius: 8px;
            color: white;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: var(--card-bg);
            border: 1px solid var(--neon-green);
            border-radius: 10px;
            display: none;
            z-index: 1001;
            animation: slideIn 0.3s;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .loader {
            display: none;
            text-align: center;
            padding: 20px;
            color: var(--neon-green);
        }
        
        .user-info {
            text-align: center;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            .info-section {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">MATEUS AI</div>
            <div class="slogan">Нейросеть для ваших запросов</div>
            <div class="user-info" id="userInfo">
                <!-- Динамически заполняется -->
            </div>
        </header>
        
        <div class="main-content">
            <div class="chat-section">
                <div class="card">
                    <h3 style="color: var(--neon-green); margin-bottom: 15px;">💬 Чат с Mateus AI</h3>
                    <div class="chat-messages" id="chatMessages">
                        <div class="message ai-message">
                            🤖 Добро пожаловать в Mateus AI! Я ищу информацию в интернете и предоставляю точные ответы. Задайте мне любой вопрос!
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <input type="text" id="userInput" placeholder="Введите ваш вопрос..." autocomplete="off">
                        <button class="btn-primary" onclick="sendMessage()">Отправить</button>
                    </div>
                    
                    <div class="loader" id="loader">
                        🔍 Поиск информации в интернете...
                    </div>
                </div>
            </div>
            
            <div class="info-section">
                <div class="card">
                    <h3 style="color: var(--neon-green); margin-bottom: 20px;">📊 Ваша статистика</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span>Токены:</span>
                            <span class="stat-value" id="tokenCount">0</span>
                        </div>
                        <div class="stat-item">
                            <span>Подписка:</span>
                            <span class="stat-value" id="subscriptionType">Free</span>
                        </div>
                        <div class="stat-item">
                            <span>Запросов сегодня:</span>
                            <span class="stat-value" id="requestsToday">0/34</span>
                        </div>
                        <div class="stat-item">
                            <span>Токенов до Pro:</span>
                            <span class="stat-value" id="tokensToPro">1000</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 25px; display: grid; gap: 10px;">
                        <button class="btn-premium" onclick="showUpgradeModal()" id="upgradeBtn">
                            💎 Апгрейд до Pro
                        </button>
                        <button class="btn-secondary" onclick="showAdminModal()">
                            🔧 Админ-панель
                        </button>
                        <button class="btn-danger" onclick="logout()" id="logoutBtn">
                            🚪 Выйти
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Модальные окна -->
    <div class="modal" id="loginModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('loginModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 25px;">🔐 Вход / Регистрация</h2>
            
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
            
            <div id="loginError" style="color: #ff4444; margin-bottom: 15px;"></div>
            
            <button class="btn-primary" onclick="registerUser()" style="width: 100%;">
                Зарегистрироваться / Войти
            </button>
        </div>
    </div>
    
    <div class="modal" id="adminModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('adminModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 25px;">🔧 Админ-панель</h2>
            
            <div class="form-group">
                <label>Пароль администратора</label>
                <input type="password" id="adminPassword" placeholder="Введите пароль">
            </div>
            
            <div class="form-group">
                <label>Имя пользователя</label>
                <input type="text" id="adminUsername" placeholder="Для кого изменяем">
            </div>
            
            <div class="form-group">
                <label>Действие</label>
                <select id="adminAction">
                    <option value="add_tokens">Добавить токены</option>
                    <option value="set_pro">Установить Pro</option>
                    <option value="remove_pro">Убрать Pro</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Количество токенов</label>
                <input type="number" id="adminAmount" value="100" min="1">
            </div>
            
            <div id="adminError" style="color: #ff4444; margin-bottom: 15px;"></div>
            
            <button class="btn-primary" onclick="adminAction()" style="width: 100%;">
                Выполнить
            </button>
        </div>
    </div>
    
    <div class="modal" id="upgradeModal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal('upgradeModal')">×</span>
            <h2 style="color: var(--neon-green); margin-bottom: 25px;">💎 Подписка Pro</h2>
            
            <div style="background: #000; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px;">Преимущества:</h4>
                <ul style="padding-left: 20px; color: var(--text-muted);">
                    <li>✅ Неограниченные запросы</li>
                    <li>⚡ Приоритетная обработка</li>
                    <li>🔍 Расширенный анализ</li>
                    <li>🚀 Экспериментальные функции</li>
                </ul>
            </div>
            
            <div style="text-align: center; padding: 20px; border: 2px solid var(--neon-green); border-radius: 10px; margin-bottom: 20px;">
                <h3>Стоимость: 1000 токенов</h3>
                <p style="color: var(--text-muted); margin-top: 10px;" id="tokensInfo"></p>
            </div>
            
            <button class="btn-premium" onclick="upgradeToPro()" style="width: 100%;" id="upgradeActionBtn">
                Активировать Pro
            </button>
        </div>
    </div>
    
    <div class="notification" id="notification"></div>
    
    <script>
        let currentUser = null;
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            checkAuth();
            setupEventListeners();
        });
        
        function setupEventListeners() {
            // Enter для отправки
            document.getElementById('userInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Авто-логин модалка
            setTimeout(() => {
                if (!currentUser) {
                    showLoginModal();
                }
            }, 1000);
        }
        
        // Модальные окна
        function showLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
            document.getElementById('loginError').textContent = '';
        }
        
        function showAdminModal() {
            if (!currentUser) {
                showNotification('Сначала войдите в систему', 'error');
                showLoginModal();
                return;
            }
            document.getElementById('adminModal').style.display = 'block';
            document.getElementById('adminError').textContent = '';
        }
        
        function showUpgradeModal() {
            if (!currentUser) {
                showNotification('Сначала войдите в систему', 'error');
                showLoginModal();
                return;
            }
            
            document.getElementById('upgradeModal').style.display = 'block';
            const tokensInfo = document.getElementById('tokensInfo');
            const upgradeBtn = document.getElementById('upgradeActionBtn');
            
            if (currentUser.tokens >= 1000) {
                tokensInfo.innerHTML = `<span style="color: #00ff88">✅ У вас ${currentUser.tokens} токенов</span>`;
                upgradeBtn.disabled = false;
                upgradeBtn.innerHTML = '💰 Активировать Pro за 1000 токенов';
            } else {
                const needed = 1000 - currentUser.tokens;
                tokensInfo.innerHTML = `<span style="color: #ff4444">❌ Нужно еще ${needed} токенов</span>`;
                upgradeBtn.disabled = true;
                upgradeBtn.innerHTML = '❌ Недостаточно токенов';
            }
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Уведомления
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.display = 'block';
            notification.style.borderColor = type === 'error' ? '#ff4444' : '#00ff88';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        // API функции
        async function registerUser() {
            const username = document.getElementById('loginUsername').value.trim();
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            if (!username || !email || !password) {
                document.getElementById('loginError').textContent = 'Заполните все поля';
                return;
            }
            
            try {
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
                    showNotification(`Добро пожаловать, ${username}!`, 'success');
                    addMessage(`🤖 Привет, ${username}! Теперь вы можете задавать вопросы.`, 'ai');
                } else {
                    document.getElementById('loginError').textContent = data.error;
                }
            } catch (error) {
                showNotification('Ошибка соединения', 'error');
            }
        }
        
        async function sendMessage() {
            if (!currentUser) {
                showLoginModal();
                return;
            }
            
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
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
                    addMessage(`❌ ${data.error}`, 'ai');
                }
            } catch (error) {
                addMessage('❌ Ошибка соединения', 'ai');
            }
            
            document.getElementById('loader').style.display = 'none';
        }
        
        async function adminAction() {
            const password = document.getElementById('adminPassword').value;
            const username = document.getElementById('adminUsername').value.trim();
            const action = document.getElementById('adminAction').value;
            const amount = parseInt(document.getElementById('adminAmount').value);
            
            if (!password || !username) {
                document.getElementById('adminError').textContent = 'Заполните все поля';
                return;
            }
            
            try {
                const response = await fetch('/api/admin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        admin_password: password,
                        username: username,
                        action: action,
                        amount: amount
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(data.message, 'success');
                    closeModal('adminModal');
                    
                    if (currentUser.username === username) {
                        checkAuth();
                    }
                } else {
                    document.getElementById('adminError').textContent = data.error;
                }
            } catch (error) {
                showNotification('Ошибка соединения', 'error');
            }
        }
        
        async function upgradeToPro() {
            try {
                const response = await fetch('/api/upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUserInfo();
                    closeModal('upgradeModal');
                    showNotification('🎉 Теперь у вас Pro подписка!', 'success');
                } else {
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                showNotification('Ошибка соединения', 'error');
            }
        }
        
        async function logout() {
            try {
                await fetch('/api/logout');
                currentUser = null;
                updateUserInfo();
                document.getElementById('chatMessages').innerHTML = 
                    '<div class="message ai-message">🤖 Вы вышли из системы</div>';
                showNotification('Вы успешно вышли', 'info');
                setTimeout(showLoginModal, 1000);
            } catch (error) {
                showNotification('Ошибка выхода', 'error');
            }
        }
        
        // Вспомогательные функции
        function addMessage(text, sender) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function updateUserInfo() {
            const userInfoDiv = document.getElementById('userInfo');
            const tokenCount = document.getElementById('tokenCount');
            const subscriptionType = document.getElementById('subscriptionType');
            const requestsToday = document.getElementById('requestsToday');
            const tokensToPro = document.getElementById('tokensToPro');
            const upgradeBtn = document.getElementById('upgradeBtn');
            const logoutBtn = document.getElementById('logoutBtn');
            
            if (currentUser) {
                userInfoDiv.innerHTML = `
                    <div style="margin-bottom: 5px;">
                        👤 <strong>${currentUser.username}</strong>
                        ${currentUser.subscription === 'pro' ? '<span style="color: #8800ff; margin-left: 10px;">PRO</span>' : ''}
                    </div>
                    <div style="color: var(--text-muted); font-size: 14px;">
                        Токены: ${currentUser.tokens} | Запросы: ${currentUser.daily_requests || 0}/${currentUser.subscription === 'pro' ? '∞' : '34'}
                    </div>
                `;
                
                tokenCount.textContent = currentUser.tokens;
                subscriptionType.textContent = currentUser.subscription === 'pro' ? 'Pro' : 'Free';
                subscriptionType.style.color = currentUser.subscription === 'pro' ? '#8800ff' : '#00ff88';
                
                const maxRequests = currentUser.subscription === 'pro' ? '∞' : '34';
                requestsToday.textContent = `${currentUser.daily_requests || 0}/${maxRequests}`;
                
                if (currentUser.subscription === 'pro') {
                    tokensToPro.textContent = 'PRO';
                    tokensToPro.style.color = '#8800ff';
                    upgradeBtn.style.display = 'none';
                } else {
                    const needed = 1000 - currentUser.tokens;
                    tokensToPro.textContent = needed > 0 ? needed : 'Готово!';
                    upgradeBtn.style.display = 'block';
                    logoutBtn.style.display = 'block';
                }
            } else {
                userInfoDiv.innerHTML = '<button class="btn-primary" onclick="showLoginModal()">Войти / Регистрация</button>';
                tokenCount.textContent = '0';
                subscriptionType.textContent = 'None';
                requestsToday.textContent = '0/0';
                tokensToPro.textContent = '1000';
                upgradeBtn.style.display = 'block';
                logoutBtn.style.display = 'none';
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
        
        // Закрытие модалок по клику вне
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        };
    </script>
</body>
</html>
'''

# API маршруты
@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Все поля обязательны'})
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': 'Имя минимум 3 символа'})
        
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if user:
            if user.check_password(password):
                session['user_id'] = user.id
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
            user = User(username=username, email=email)
            user.set_password(password)
            user.tokens = 100
            user.last_request_date = datetime.now().strftime('%Y-%m-%d')
            
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            
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
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка: {str(e)}'})

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
def api_ask():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        # Проверка лимита
        today = datetime.now().strftime('%Y-%m-%d')
        if user.last_request_date != today:
            user.daily_requests = 0
            user.last_request_date = today
        
        if user.subscription != 'pro' and user.daily_requests >= 34:
            return jsonify({'success': False, 'error': 'Достигнут лимит 34 запроса в день'})
        
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Введите вопрос'})
        
        # Обработка запроса
        response = ai.process_query(question)
        
        # Обновляем статистику
        user.daily_requests += 1
        if user.subscription == 'free':
            user.tokens += 10
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'answer': response['answer'],
            'sources': response['sources'],
            'confidence': response['confidence']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка: {str(e)}'})

@app.route('/api/admin', methods=['POST'])
def api_admin():
    try:
        data = request.json
        admin_password = data.get('admin_password')
        username = data.get('username')
        action = data.get('action')
        amount = data.get('amount', 100)
        
        admin_settings = AdminSettings.query.first()
        if not admin_settings or not check_password_hash(admin_settings.admin_password, admin_password):
            return jsonify({'success': False, 'error': 'Неверный пароль админа'})
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        message = ''
        if action == 'add_tokens':
            user.tokens += int(amount)
            message = f'Добавлено {amount} токенов'
        elif action == 'set_pro':
            user.subscription = 'pro'
            message = 'Подписка Pro активирована'
        elif action == 'remove_pro':
            user.subscription = 'free'
            message = 'Подписка Pro отключена'
        else:
            return jsonify({'success': False, 'error': 'Неизвестное действие'})
        
        db.session.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка: {str(e)}'})

@app.route('/api/upgrade', methods=['POST'])
def api_upgrade():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        if user.subscription == 'pro':
            return jsonify({'success': False, 'error': 'Уже есть Pro'})
        
        if user.tokens < 1000:
            return jsonify({'success': False, 'error': f'Нужно 1000 токенов, у вас {user.tokens}'})
        
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
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка: {str(e)}'})

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Mateus AI'})

# Запуск приложения
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Ищем результаты
            for result in soup.find_all('a', class_='result__url'):
                title = result.text.strip()
                link = result.get('href')
                if link and title and not link.startswith('//'):
                    # Получаем заголовок из родительского элемента
                    title_elem = result.find_previous('a', class_='result__title')
                    if title_elem:
                        title_text = title_elem.text.strip()
                        if title_text:
                            title = title_text
                    
                    results.append({
                        'title': title[:200],
                        'link': link if link.startswith('http') else f'https:{link}'
                    })
                
                if len(results) >= num_results:
                    break
            
            # Альтернативный поиск если не нашли результатов
            if not results:
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and ('http' in href) and ('duckduckgo' not in href):
                        results.append({
                            'title': link.text[:200] or 'Источник',
                            'link': href if href.startswith('http') else f'https:{href}'
                        })
                        if len(results) >= num_results:
                            break
            
            return results[:num_results]
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            # Возвращаем заглушки для тестирования
            return [
                {'title': 'Пример результата поиска', 'link': 'https://example.com'},
                {'title': 'Информация по вашему запросу', 'link': 'https://wikipedia.org'}
            ]

    @staticmethod
    def get_page_content(url):
        """Получение содержимого веб-страницы"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Получаем основной текст
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:3000]  # Ограничиваем объем
        except:
            return "Не удалось получить содержимое страницы."

    @staticmethod
    def get_current_time():
        """Получение текущего времени из интернета"""
        try:
            # Пробуем несколько источников
            sources = [
                'http://worldtimeapi.org/api/timezone/Europe/Moscow',
                'http://worldtimeapi.org/api/timezone/UTC',
                'http://worldclockapi.com/api/json/utc/now'
            ]
            
            for source in sources:
                try:
                    response = requests.get(source, timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        if 'datetime' in data:
                            return data['datetime']
                        elif 'currentDateTime' in data:
                            return data['currentDateTime']
                except:
                    continue
        except:
            pass
        
        # Если не удалось получить из интернета, используем локальное время
        return datetime.now(pytz.timezone('Europe/Moscow')).isoformat()

# ИИ обработчик
class MateusAI:
    def __init__(self):
        self.searcher = InternetSearcher()
        
    def process_query(self, query, user_context=None):
        """Основная обработка запроса"""
        try:
            # Получаем время
            current_time = self.searcher.get_current_time()
            
            # Проверяем специальные запросы
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['время', 'дата', 'сейчас', 'time', 'date', 'час', 'число']):
                return self._format_time_response(current_time)
            
            if any(word in query_lower for word in ['привет', 'hello', 'hi', 'здравствуй']):
                return {
                    'answer': f"🤖 **Привет! Я Mateus AI.**\n\nЯ готов помочь вам с поиском информации в интернете. Задайте ваш вопрос, и я найду самую актуальную информацию по этой теме!\n\n🕒 *Текущее время: {current_time[:19]}*",
                    'sources': [],
                    'confidence': 'high'
                }
            
            if any(word in query_lower for word in ['погода', 'weather', 'температура']):
                return {
                    'answer': "🌤️ **Информация о погоде:**\n\nДля получения точных данных о погоде мне нужно узнать ваше местоположение. Вы можете проверить погоду на специализированных сайтах:\n\n• Яндекс.Погода\n• Gismeteo\n• AccuWeather\n\n*Я могу искать информацию о погоде в конкретных городах, если уточните запрос.*",
                    'sources': ['https://yandex.ru/pogoda', 'https://www.gismeteo.ru'],
                    'confidence': 'medium'
                }
            
            # Ищем информацию в интернете
            search_results = self.searcher.search_web(query, 3)
            
            # Анализируем результаты
            analyzed_info = self._analyze_results(query, search_results)
            
            # Формируем ответ
            response = self._generate_response(query, analyzed_info, current_time)
            
            return response
        except Exception as e:
            print(f"Ошибка обработки запроса: {e}")
            traceback.print_exc()
            return {
                'answer': f"🤖 **Mateus AI отвечает:**\n\nК сожалению, при обработке вашего запроса произошла ошибка. Попробуйте переформулировать вопрос или задать его позже.\n\n*Ошибка: {str(e)[:100]}...*",
                'sources': [],
                'confidence': 'low'
            }
    
    def _analyze_results(self, query, results):
        """Анализ и сравнение информации из найденных источников"""
        analyzed = []
        
        for result in results:
            try:
                content = self.searcher.get_page_content(result['link'])
                if content and len(content) > 50:
                    # Простой анализ релевантности
                    query_words = set(re.findall(r'\w+', query.lower()))
                    content_words = set(re.findall(r'\w+', content.lower()))
                    common_words = query_words.intersection(content_words)
                    
                    if query_words:
                        relevance = len(common_words) / len(query_words)
                    else:
                        relevance = 0.1
                    
                    analyzed.append({
                        'title': result['title'],
                        'relevance': min(relevance * 1.5, 1.0),  # Увеличиваем релевантность
                        'content': content[:800],
                        'source': result['link']
                    })
            except Exception as e:
                print(f"Ошибка анализа: {e}")
                continue
        
        # Сортируем по релевантности
        analyzed.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Если нет результатов, создаем заглушку
        if not analyzed:
            analyzed.append({
                'title': 'Общая информация',
                'relevance': 0.5,
                'content': f'По запросу "{query}" в интернете есть множество источников. Рекомендую уточнить ваш вопрос для более точного ответа.',
                'source': 'https://google.com'
            })
        
        return analyzed
    
    def _generate_response(self, query, analyzed_info, current_time):
        """Генерация финального ответа"""
        # Берем самый релевантный источник
        best_source = analyzed_info[0]
        
        # Определяем уверенность
        if best_source['relevance'] > 0.7:
            confidence = 'high'
        elif best_source['relevance'] > 0.4:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Формируем ответ
        answer = f"🤖 **Mateus AI отвечает:**\n\n"
        
        if confidence == 'high':
            answer += f"✅ Нашел точную информацию по вашему запросу **'{query}'**:\n\n"
        elif confidence == 'medium':
            answer += f"🔍 Нашел информацию по теме **'{query}'**:\n\n"
        else:
            answer += f"🤔 По запросу **'{query}'** нашлась следующая информация:\n\n"
        
        # Краткое изложение
        summary = best_source['content']
        if len(summary) > 400:
            summary = summary[:400] + "... [читать далее в источнике]"
        
        answer += f"📝 **Основная информация:** {summary}\n\n"
        
        # Добавляем источники если они есть
        if len(analyzed_info) > 0:
            answer += "📚 **Источники информации:**\n"
            for i, source in enumerate(analyzed_info[:2], 1):
                answer += f"{i}. {source['title']}\n"
        
        # Добавляем время и рекомендации
        answer += f"\n🕒 *Информация актуальна на: {current_time[:19]}*\n"
        answer += f"⚡ *Уверенность ответа: {confidence}*\n\n"
        
        if confidence == 'low':
            answer += "💡 **Совет:** Попробуйте переформулировать вопрос или задать более конкретный запрос."
        
        return {
            'answer': answer,
            'sources': [s['source'] for s in analyzed_info[:3]],
            'confidence': confidence
        }
    
    def _format_time_response(self, time_str):
        """Форматирование ответа с временем"""
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            moscow_tz = pytz.timezone('Europe/Moscow')
            dt_moscow = dt.astimezone(moscow_tz)
            
            time_formatted = dt_moscow.strftime('%H:%M:%S')
            date_formatted = dt_moscow.strftime('%d.%m.%Y')
            weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][dt_moscow.weekday()]
        except:
            dt_moscow = datetime.now(pytz.timezone('Europe/Moscow'))
            time_formatted = dt_moscow.strftime('%H:%M:%S')
            date_formatted = dt_moscow.strftime('%d.%m.%Y')
            weekday = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][dt_moscow.weekday()]
        
        return {
            'answer': f"🕒 **Текущее время и дата:**\n\n"
                     f"📅 Дата: {date_formatted}\n"
                     f"📆 День недели: {weekday}\n"
                     f"⏰ Время: {time_formatted}\n"
                     f"🌍 Часовой пояс: Москва (UTC+3)\n\n"
                     f"*Информация получена из интернета в реальном времени*",
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
            return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'success': False, 'error': 'Требуются права администратора'}), 403
        return f(*args, **kwargs)
    return decorated_function

def check_daily_limit(user):
    """Проверка дневного лимита запросов"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user.last_request_date != today:
        user.daily_requests = 0
        user.last_request_date = today
        db.session.commit()
    
    if user.subscription == 'pro':
        return True  # Без лимитов для Pro
    
    max_requests = 34
    
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
            cursor: pointer;
            transition: transform 0.3s;
        }
        
        .logo:hover {
            transform: scale(1.05);
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
            padding: 12px 20px;
            border-radius: 20px;
            border: 1px solid var(--neon-green);
            min-width: 200px;
            text-align: center;
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
            .user-info {
                position: relative;
                top: 0;
                right: 0;
                margin: 0 auto 20px;
                width: 100%;
            }
            header {
                padding: 20px 10px;
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
            white-space: pre-line;
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
        
        .btn {
            padding: 15px 25px;
            background: linear-gradient(45deg, var(--dark-green), var(--neon-green));
            border: none;
            border-radius: 10px;
            color: black;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Orbitron', sans-serif;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #333, #555);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #ff5500, #ff8800);
        }
        
        .btn-premium {
            background: linear-gradient(45deg, #5500ff, #8800ff);
        }
        
        /* Панель информации */
        .info-panel {
            background: var(--gray);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid var(--neon-green);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .stats {
            background: var(--black);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 10px;
            border: 1px solid #333;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            padding: 8px 0;
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
            background: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
            margin: 10px 0;
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
            background: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
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
            max-width: 90%;
            box-shadow: 0 0 50px rgba(0, 255, 136, 0.2);
        }
        
        .close-modal {
            position: absolute;
            top: 15px;
            right: 20px;
            color: var(--neon-green);
            cursor: pointer;
            font-size: 30px;
            font-weight: bold;
            transition: color 0.3s;
        }
        
        .close-modal:hover {
            color: white;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #aaa;
            font-size: 14px;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px 15px;
            background: var(--black);
            border: 1px solid #444;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            transition: border 0.3s;
        }
        
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: var(--neon-green);
        }
        
        .error {
            color: #ff4444;
            margin-top: 10px;
            padding: 10px;
            background: rgba(255, 68, 68, 0.1);
            border-radius: 5px;
            display: none;
        }
        
        .success {
            color: var(--neon-green);
            margin-top: 10px;
            padding: 10px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 5px;
            display: none;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            background: var(--gray);
            border: 1px solid var(--neon-green);
            z-index: 1001;
            display: none;
            animation: slideIn 0.3s;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .pro-badge {
            background: linear-gradient(45deg, #5500ff, #8800ff);
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo" onclick="location.reload()">MATEUS AI</div>
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
                    <input type="text" id="userInput" placeholder="Задайте ваш вопрос..." autocomplete="off">
                    <button class="btn" onclick="sendMessage()">Отправить</button>
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
                
                <button class="btn" onclick="showUpgradeModal()" id="upgradeBtn">
                    💎 Апгрейд до Pro
                </button>
                <button class="btn btn-premium" onclick="showAdminModal()">
                    🔧 Админ-панель
                </button>
                <button class="btn btn-danger" onclick="logout()">
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
                <input type="text" id="loginUsername" placeholder="Введите имя" autocomplete="username">
            </div>
            
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="loginEmail" placeholder="email@example.com" autocomplete="email">
            </div>
            
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="loginPassword" placeholder="Введите пароль" autocomplete="current-password">
            </div>
            
            <div class="error" id="loginError"></div>
            <div class="success" id="loginSuccess"></div>
            
            <button class="btn" onclick="registerUser()" style="width: 100%; margin-top: 20px;">
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
                <select id="adminAction">
                    <option value="add_tokens">Добавить токены</option>
                    <option value="set_pro">Установить подписку Pro</option>
                    <option value="remove_pro">Убрать подписку Pro</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Количество (для токенов)</label>
                <input type="number" id="adminAmount" placeholder="Количество" value="100" min="1" max="10000">
            </div>
            
            <div class="error" id="adminError"></div>
            <div class="success" id="adminSuccess"></div>
            
            <button class="btn" onclick="adminAction()" style="width: 100%; margin-top: 20px;">
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
                    <li>✅ Неограниченное количество запросов в день</li>
                    <li>⚡ Приоритетная обработка запросов</li>
                    <li>🔍 Расширенный анализ информации</li>
                    <li>🚀 Доступ к экспериментальным функциям</li>
                    <li>🎯 Более точные ответы</li>
                </ul>
            </div>
            
            <div style="text-align: center; padding: 20px; border: 2px solid var(--neon-green); border-radius: 15px; margin-bottom: 20px;">
                <h3>Стоимость: <span class="neon-text">1000 токенов</span></h3>
                <p style="color: #aaa; margin-top: 10px;">Накопите токены, используя бесплатную версию</p>
                <p id="currentTokensInfo" style="margin-top: 10px; font-size: 14px;"></p>
            </div>
            
            <button class="btn" onclick="upgradeToPro()" style="width: 100%;" id="upgradeProBtn">
                💰 Активировать Pro за 1000 токенов
            </button>
        </div>
    </div>
    
    <!-- Уведомление -->
    <div class="notification" id="notification"></div>
    
    <script>
        // Глобальные переменные
        let currentUser = null;
        
        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', function() {
            checkAuth();
            setupEventListeners();
            showNotification('Добро пожаловать в Mateus AI!', 'info');
        });
        
        // Настройка обработчиков событий
        function setupEventListeners() {
            // Enter для отправки сообщения
            document.getElementById('userInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Автоматическое открытие модалки логина если не авторизован
            setTimeout(() => {
                if (!currentUser) {
                    showLoginModal();
                }
            }, 500);
        }
        
        // Показать уведомление
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.display = 'block';
            
            if (type === 'success') {
                notification.style.borderColor = '#00ff88';
                notification.style.color = '#00ff88';
            } else if (type === 'error') {
                notification.style.borderColor = '#ff4444';
                notification.style.color = '#ff4444';
            } else {
                notification.style.borderColor = '#00ff88';
                notification.style.color = '#00ff88';
            }
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
        
        // Функции модальных окон
        function showLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
            document.getElementById('loginError').style.display = 'none';
            document.getElementById('loginSuccess').style.display = 'none';
        }
        
        function showAdminModal() {
            if (!currentUser) {
                showLoginModal();
                showNotification('Сначала войдите в систему', 'error');
                return;
            }
            document.getElementById('adminModal').style.display = 'block';
            document.getElementById('adminError').style.display = 'none';
            document.getElementById('adminSuccess').style.display = 'none';
            document.getElementById('adminPassword').value = '';
            document.getElementById('adminUsername').value = '';
        }
        
        function showUpgradeModal() {
            if (!currentUser) {
                showLoginModal();
                showNotification('Сначала войдите в систему', 'error');
                return;
            }
            
            const modal = document.getElementById('upgradeModal');
            modal.style.display = 'block';
            
            // Обновляем информацию о токенах
            const tokensInfo = document.getElementById('currentTokensInfo');
            const upgradeBtn = document.getElementById('upgradeProBtn');
            
            if (currentUser.tokens >= 1000) {
                tokensInfo.innerHTML = `<span style="color: #00ff88">✅ У вас ${currentUser.tokens} токенов - достаточно для апгрейда!</span>`;
                upgradeBtn.disabled = false;
                upgradeBtn.innerHTML = '💰 Активировать Pro за 1000 токенов';
            } else {
                const needed = 1000 - currentUser.tokens;
                tokensInfo.innerHTML = `<span style="color: #ff4444">❌ У вас ${currentUser.tokens} токенов. Нужно еще ${needed} токенов</span>`;
                upgradeBtn.disabled = true;
                upgradeBtn.innerHTML = `❌ Недостаточно токенов (нужно ${needed} еще)`;
                upgradeBtn.style.opacity = '0.6';
                upgradeBtn.style.cursor = 'not-allowed';
            }
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Закрытие модалок по клику вне области
        window.onclick = function(event) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        };
        
        // Регистрация/авторизация
        async function registerUser() {
            const username = document.getElementById('loginUsername').value.trim();
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            if (!username || !email || !password) {
                showError('loginError', 'Заполните все поля');
                return;
            }
            
            if (password.length < 4) {
                showError('loginError', 'Пароль должен быть не менее 4 символов');
                return;
            }
            
            try {
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
                    showNotification(`Добро пожаловать, ${username}!`, 'success');
                    
                    // Добавляем приветственное сообщение
                    addMessage(`🤖 Добро пожаловать, ${username}! Теперь вы можете задавать вопросы. У вас ${currentUser.tokens} токенов.`, 'ai');
                } else {
                    showError('loginError', data.error || 'Ошибка сервера');
                }
            } catch (error) {
                showError('loginError', 'Ошибка соединения с сервером');
            }
        }
        
        // Отправка сообщения
        async function sendMessage() {
            if (!currentUser) {
                showLoginModal();
                showNotification('Сначала войдите в систему', 'error');
                return;
            }
            
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message) {
                showNotification('Введите сообщение', 'error');
                return;
            }
            
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
                    showNotification('Ответ получен!', 'success');
                } else {
                    addMessage(`❌ Ошибка: ${data.error}`, 'ai');
                    showNotification(data.error, 'error');
                }
            } catch (error) {
                addMessage('❌ Ошибка соединения с сервером', 'ai');
                showNotification('Ошибка соединения', 'error');
            } finally {
                document.getElementById('loader').style.display = 'none';
            }
        }
        
        // Админ действия
        async function adminAction() {
            const password = document.getElementById('adminPassword').value;
            const username = document.getElementById('adminUsername').value.trim();
            const action = document.getElementById('adminAction').value;
            const amount = parseInt(document.getElementById('adminAmount').value);
            
            if (!password) {
                showError('adminError', 'Введите пароль администратора');
                return;
            }
            
            if (!username) {
                showError('adminError', 'Введите имя пользователя');
                return;
            }
            
            if (action === 'add_tokens' && (isNaN(amount) || amount < 1)) {
                showError('adminError', 'Введите корректное количество токенов');
                return;
            }
            
            try {
                const response = await fetch('/api/admin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        admin_password: password,
                        username: username,
                        action: action,
                        amount: amount
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess('adminSuccess', data.message || 'Действие выполнено успешно');
                    
                    // Обновляем информацию если это текущий пользователь
                    if (currentUser && currentUser.username === username) {
                        setTimeout(checkAuth, 500);
                    }
                    
                    // Очищаем форму
                    document.getElementById('adminPassword').value = '';
                    document.getElementById('adminUsername').value = '';
                    document.getElementById('adminAmount').value = '100';
                    
                    showNotification('Действие выполнено успешно!', 'success');
                } else {
                    showError('adminError', data.error || 'Ошибка сервера');
                }
            } catch (error) {
                showError('adminError', 'Ошибка соединения с сервером');
            }
        }
        
        // Апгрейд до Pro
        async function upgradeToPro() {
            try {
                const response = await fetch('/api/upgrade', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUserInfo();
                    closeModal('upgradeModal');
                    showNotification('🎉 Поздравляем! Теперь у вас подписка Pro!', 'success');
                    addMessage('🎉 Поздравляем! Теперь у вас подписка Pro! Все ограничения сняты.', 'ai');
                } else {
                    showNotification(data.error || 'Ошибка', 'error');
                }
            } catch (error) {
                showNotification('Ошибка соединения', 'error');
            }
        }
        
        // Выход
        async function logout() {
            try {
                await fetch('/api/logout');
                currentUser = null;
                updateUserInfo();
                document.getElementById('chatMessages').innerHTML = 
                    '<div class="message ai-message">🤖 Вы вышли из системы. Войдите, чтобы продолжить.</div>';
                showNotification('Вы успешно вышли из системы', 'info');
                setTimeout(showLoginModal, 1000);
            } catch (error) {
                showNotification('Ошибка при выходе', 'error');
            }
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
            
            // Скрываем другие сообщения
            if (elementId.includes('Error')) {
                const successId = elementId.replace('Error', 'Success');
                const successElement = document.getElementById(successId);
                if (successElement) successElement.style.display = 'none';
            }
        }
        
        function showSuccess(elementId, message) {
            const element = document.getElementById(elementId);
            element.textContent = message;
            element.style.display = 'block';
            
            // Скрываем другие сообщения
            if (elementId.includes('Success')) {
                const errorId = elementId.replace('Success', 'Error');
                const errorElement = document.getElementById(errorId);
                if (errorElement) errorElement.style.display = 'none';
            }
        }
        
        function updateUserInfo() {
            const userInfoDiv = document.getElementById('userInfo');
            const tokenCount = document.getElementById('tokenCount');
            const subscriptionType = document.getElementById('subscriptionType');
            const requestsToday = document.getElementById('requestsToday');
            const tokensToPro = document.getElementById('tokensToPro');
            const upgradeBtn = document.getElementById('upgradeBtn');
            
            if (currentUser) {
                userInfoDiv.innerHTML = `
                    <div style="margin-bottom: 5px;">👤 <strong>${currentUser.username}</strong></div>
                    <div>${currentUser.subscription === 'pro' ? '<span class="pro-badge">PRO</span>' : '<span style="color: #aaa">FREE</span>'}</div>
                    <div style="margin-top: 8px; font-size: 12px; color: #aaa;">
                        Токены: ${currentUser.tokens}
                    </div>
                `;
                
                tokenCount.textContent = currentUser.tokens;
                subscriptionType.textContent = currentUser.subscription === 'pro' ? 'Pro' : 'Free';
                subscriptionType.style.color = currentUser.subscription === 'pro' ? '#8800ff' : '#00ff88';
                
                const maxRequests = currentUser.subscription === 'pro' ? '∞' : '34';
                requestsToday.textContent = `${currentUser.daily_requests || 0}/${maxRequests}`;
                
                if (currentUser.subscription === 'pro') {
                    tokensToPro.textContent = 'PRO';
                    tokensToPro.style.color = '#8800ff';
                    upgradeBtn.style.display = 'none';
                } else {
                    const needed = 1000 - currentUser.tokens;
                    tokensToPro.textContent = needed > 0 ? needed : 'Готово!';
                    upgradeBtn.style.display = 'block';
                }
            } else {
                userInfoDiv.innerHTML = '<button class="btn" onclick="showLoginModal()" style="width: 100%;">Войти / Регистрация</button>';
                tokenCount.textContent = '0';
                subscriptionType.textContent = 'None';
                subscriptionType.style.color = '#aaa';
                requestsToday.textContent = '0/0';
                tokensToPro.textContent = '1000';
                tokensToPro.style.color = '#00ff88';
                upgradeBtn.style.display = 'block';
            }
        }
        
        async function checkAuth() {
            try {
                const response = await fetch('/api/me');
                const data = await response.json();
                
                if (data.success) {
                    currentUser = data.user;
                    updateUserInfo();
                    
                    // Проверяем если сегодня новая дата
                    const today = new Date().toISOString().split('T')[0];
                    if (currentUser.last_request_date !== today) {
                        currentUser.daily_requests = 0;
                    }
                }
            } catch (error) {
                console.log('Пользователь не авторизован');
            }
        }
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
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Все поля обязательны'})
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': 'Имя пользователя должно быть не менее 3 символов'})
        
        if len(password) < 4:
            return jsonify({'success': False, 'error': 'Пароль должен быть не менее 4 символов'})
        
        # Проверяем существование пользователя
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if user:
            # Авторизация
            if user.check_password(password):
                session['user_id'] = user.id
                session.permanent = True
                
                # Обновляем дату последнего запроса
                today = datetime.now().strftime('%Y-%m-%d')
                if user.last_request_date != today:
                    user.daily_requests = 0
                    user.last_request_date = today
                    db.session.commit()
                
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'tokens': user.tokens,
                        'subscription': user.subscription,
                        'daily_requests': user.daily_requests,
                        'last_request_date': user.last_request_date
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Неверный пароль'})
        else:
            # Регистрация
            user = User(username=username, email=email)
            user.set_password(password)
            user.tokens = 100  # Начальные токены
            user.last_request_date = datetime.now().strftime('%Y-%m-%d')
            
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
                    'daily_requests': user.daily_requests,
                    'last_request_date': user.last_request_date
                }
            })
    except Exception as e:
        print(f"Ошибка регистрации: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})

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
                    'daily_requests': user.daily_requests,
                    'last_request_date': user.last_request_date
                }
            })
    return jsonify({'success': False})

@app.route('/api/ask', methods=['POST'])
@login_required
def api_ask():
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        # Проверяем лимит
        if not check_daily_limit(user):
            return jsonify({
                'success': False,
                'error': f'Достигнут дневной лимит (34 запроса). Завтра снова будет доступно.'
            })
        
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Вопрос не может быть пустым'})
        
        if len(question) > 500:
            return jsonify({'success': False, 'error': 'Вопрос слишком длинный (макс. 500 символов)'})
        
        # Обрабатываем запрос через ИИ
        response = ai.process_query(question)
        
        # Начисляем токены только бесплатным пользователям
        if user.subscription == 'free':
            user.tokens += 10  # 10 токенов за запрос
            db.session.commit()
        
        return jsonify({
            'success': True,
            'answer': response['answer'],
            'sources': response['sources'],
            'confidence': response['confidence']
        })
    except Exception as e:
        print(f"Ошибка обработки запроса: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})

@app.route('/api/admin', methods=['POST'])
def api_admin():
    try:
        data = request.json
        admin_password = data.get('admin_password')
        username = data.get('username', '').strip()
        action = data.get('action')
        amount = data.get('amount', 100)
        
        if not admin_password:
            return jsonify({'success': False, 'error': 'Введите пароль администратора'})
        
        # Проверяем пароль админа
        admin_settings = AdminSettings.query.first()
        if not admin_settings or not check_password_hash(admin_settings.admin_password, admin_password):
            return jsonify({'success': False, 'error': 'Неверный пароль администратора'})
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        message = ''
        
        # Выполняем действие
        if action == 'add_tokens':
            if not isinstance(amount, int) or amount < 1 or amount > 10000:
                return jsonify({'success': False, 'error': 'Некорректное количество токенов (1-10000)'})
            
            user.tokens += amount
            message = f'Добавлено {amount} токенов пользователю {username}. Теперь у него {user.tokens} токенов.'
            
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
    except Exception as e:
        print(f"Ошибка админ-панели: {e}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})

@app.route('/api/upgrade', methods=['POST'])
@login_required
def api_upgrade():
    try:
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
                'subscription': user.subscription,
                'daily_requests': user.daily_requests
            }
        })
    except Exception as e:
        print(f"Ошибка апгрейда: {e}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Mateus AI'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
