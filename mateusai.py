"""
Mateus AI - Версия для деплоя на Render.com
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

# Настройки для Render.com
if os.environ.get('RENDER'):
    # На Render используем PostgreSQL или внешнее хранилище
    print("🚀 Запуск на Render.com")
    # Для хранения данных используем переменные окружения
    USERS_DATA = os.environ.get('USERS_DATA', '{}')
    SETTINGS_DATA = os.environ.get('SETTINGS_DATA', '{}')
else:
    # Локальный запуск
    USERS_DATA = '{}'
    SETTINGS_DATA = '{}'

# Инициализация OpenAI
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ ERROR: OPENAI_API_KEY environment variable is required!")
    # Для Render можно использовать значение по умолчанию для тестирования
    openai_api_key = "sk-test" if os.environ.get('RENDER') else None

openai.api_key = openai_api_key
try:
    client = OpenAI(api_key=openai_api_key)
except:
    print("⚠️  Warning: OpenAI client initialization failed")
    client = None

# Конфигурация DonationAlerts
DONATION_ALERTS = {
    'client_id': os.environ.get('DA_CLIENT_ID', ''),
    'client_secret': os.environ.get('DA_CLIENT_SECRET', ''),
    'redirect_uri': os.environ.get('DA_REDIRECT_URI', os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:3498') + '/donation/callback'),
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
if not ADMIN_PASSWORD and os.environ.get('RENDER'):
    print("⚠️  Warning: ADMIN_PASSWORD not set on Render!")

# ==================== УТИЛИТЫ ДЛЯ RENDER ====================

class RenderDataStore:
    """Класс для хранения данных на Render.com"""
    
    def __init__(self):
        self.users = self._load_from_env('USERS_DATA')
        self.settings = self._load_from_env('SETTINGS_DATA')
        self.donations = self._load_from_env('DONATIONS_DATA', {})
    
    def _load_from_env(self, env_var, default={}):
        """Загрузка данных из переменной окружения"""
        data_str = os.environ.get(env_var, '{}')
        try:
            if data_str and data_str != '{}':
                return json.loads(data_str)
        except:
            print(f"⚠️  Error loading {env_var}")
        return default.copy()
    
    def save_users(self):
        """Сохранение пользователей в переменную окружения (в реальном приложении используйте базу данных)"""
        # В реальном приложении используйте базу данных PostgreSQL
        # Здесь упрощенная версия для демонстрации
        return True
    
    def save_settings(self):
        """Сохранение настроек"""
        return True

# Инициализация хранилища
if os.environ.get('RENDER'):
    data_store = RenderDataStore()
    users_db = data_store.users
    settings_db = data_store.settings
    donations_db = data_store.donations
else:
    # Локальное хранение в файлах
    USERS_FILE = 'users.json'
    DONATIONS_FILE = 'donations.json'
    SETTINGS_FILE = 'settings.json'
    
    def ensure_files_exist():
        for filename in [USERS_FILE, DONATIONS_FILE, SETTINGS_FILE]:
            if not os.path.exists(filename):
                default_data = {}
                if filename == SETTINGS_FILE:
                    default_data = {
                        'donation_alerts': {'connected': False, 'access_token': '', 'refresh_token': ''},
                        'pro_codes': {}
                    }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    ensure_files_exist()
    
    def load_data(filename, default={}):
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default.copy()
    
    def save_data(filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    users_db = load_data(USERS_FILE)
    settings_db = load_data(SETTINGS_FILE, {
        'donation_alerts': {'connected': False, 'access_token': '', 'refresh_token': ''},
        'pro_codes': {}
    })
    donations_db = load_data(DONATIONS_FILE)

# ==================== HTML ШАБЛОНЫ (сокращенная версия для Render) ====================

BASE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #1a5d1a; --secondary: #2e8b57;
            --light: #90ee90; --accent: #32cd32;
            --dark: #0d3b0d; --background: #0a1a0a;
            --card: #162416; --text: #f0fff0;
            --muted: #a3d9a3; --border: #2a5c2a;
            --gold: #ffd700; --blue: #4dabf7;
            --purple: #9775fa; --red: #ff6b6b;
        }
        
        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--background);
            color: var(--text);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, var(--primary), var(--dark));
            border-radius: 20px;
            margin-bottom: 30px;
            border: 2px solid var(--accent);
        }
        
        .logo {
            font-size: 3rem;
            color: var(--light);
            margin-bottom: 10px;
        }
        
        .title {
            font-size: 2.5rem;
            background: linear-gradient(45deg, var(--light), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: var(--card);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
        }
        
        .btn {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(46, 139, 87, 0.4);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--accent), var(--light));
            color: var(--dark);
        }
        
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            border: 1px solid var(--border);
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 12px;
            max-width: 80%;
        }
        
        .user-message {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            margin-left: auto;
            color: white;
        }
        
        .ai-message {
            background: rgba(46, 139, 87, 0.2);
            border: 1px solid var(--border);
            margin-right: auto;
        }
        
        .chat-input {
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-size: 1rem;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: var(--muted);
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }
        
        .alert {
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            border-left: 4px solid;
        }
        
        .alert-success {
            border-color: var(--accent);
            background: rgba(50, 205, 50, 0.1);
        }
        
        .alert-error {
            border-color: var(--red);
            background: rgba(255, 107, 107, 0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        {header}
        <div class="main-content">
            {sidebar}
            {content}
        </div>
        {footer}
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Отправка сообщения
            window.sendMessage = function() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Добавляем сообщение пользователя
                addMessage('user', message);
                input.value = '';
                
                // Показываем индикатор загрузки
                addMessage('ai', '<i class="fas fa-spinner fa-spin"></i> Думаю...');
                
                // Отправляем на сервер
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                })
                .then(r => r.json())
                .then(data => {
                    // Удаляем индикатор загрузки
                    const chat = document.getElementById('chatMessages');
                    chat.lastChild.remove();
                    
                    if (data.success) {
                        addMessage('ai', data.response);
                    } else {
                        addMessage('ai', '<div class="alert alert-error">' + (data.error || 'Ошибка') + '</div>');
                    }
                })
                .catch(error => {
                    const chat = document.getElementById('chatMessages');
                    if (chat.lastChild.innerHTML.includes('fa-spin')) {
                        chat.lastChild.remove();
                    }
                    addMessage('ai', '<div class="alert alert-error">Ошибка сети</div>');
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
                if (!code) return alert('Введите код');
                
                fetch('/activate_pro', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({code: code})
                })
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    if (data.success) location.reload();
                });
            };
        });
        
        function addMessage(sender, text) {
            const chat = document.getElementById('chatMessages');
            if (!chat) return;
            
            const div = document.createElement('div');
            div.className = `message ${sender}-message`;
            div.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 5px;">
                    ${sender === 'user' ? '👤 Вы' : '🤖 Mateus AI'}
                </div>
                <div>${text}</div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
'''

def render_page(title, header, sidebar, content, footer):
    return render_template_string(BASE_HTML, title=title, header=header, sidebar=sidebar, content=content, footer=footer)

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

def get_user_id():
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
    
    if user_id not in users_db:
        users_db[user_id] = {
            'id': user_id,
            'created': datetime.now().isoformat(),
            'requests_today': 0,
            'last_request': datetime.now().date().isoformat(),
            'is_pro': False,
            'pro_until': None,
            'limit': FREE_LIMIT,
            'total_requests': 0
        }
        if not os.environ.get('RENDER'):
            save_data(USERS_FILE, users_db)
    
    return user_id

def check_request_limit(user_id):
    if user_id not in users_db:
        get_user_id()
    
    user = users_db.get(user_id, {})
    today = datetime.now().date().isoformat()
    
    if user.get('last_request') != today:
        user['requests_today'] = 0
        user['last_request'] = today
    
    limit = PRO_LIMIT if user.get('is_pro') else FREE_LIMIT
    return user['requests_today'] < limit, limit, user['requests_today']

def increment_request(user_id):
    user = users_db.get(user_id)
    if user:
        user['requests_today'] = user.get('requests_today', 0) + 1
        user['total_requests'] = user.get('total_requests', 0) + 1
        user['last_request'] = datetime.now().date().isoformat()
        if not os.environ.get('RENDER'):
            save_data(USERS_FILE, users_db)

# Роли AI
ROLES = {
    'assistant': 'Ты - умный помощник Mateus AI. Отвечай подробно и полезно.',
    'psychologist': 'Ты - профессиональный психолог. Помогай с эмоциональными вопросами.',
    'teacher': 'Ты - опытный учитель. Объясняй сложные темы просто.',
    'programmer': 'Ты - senior разработчик. Помогай с кодом и технологиями.',
    'scientist': 'Ты - учёный. Объясняй научные концепции точно.'
}

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used = check_request_limit(user_id)
    remaining = limit - used
    
    header = f'''
    <div class="header">
        <div class="logo"><i class="fas fa-brain"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p>Запросов: {used}/{limit} | Осталось: {remaining}</p>
        {'<p style="color: var(--gold);"><i class="fas fa-crown"></i> PRO активен</p>' if user.get('is_pro') else ''}
    </div>
    '''
    
    sidebar = f'''
    <div class="card">
        <h3>Выберите роль:</h3>
        <div style="display: flex; flex-direction: column; gap: 10px; margin: 15px 0;">
            <button class="btn" onclick="selectRole('assistant')"><i class="fas fa-robot"></i> Помощник</button>
            <button class="btn" onclick="selectRole('psychologist')"><i class="fas fa-heart"></i> Психолог</button>
            <button class="btn" onclick="selectRole('teacher')"><i class="fas fa-graduation-cap"></i> Учитель</button>
            <button class="btn" onclick="selectRole('programmer')"><i class="fas fa-code"></i> Программист</button>
            <button class="btn" onclick="selectRole('scientist')"><i class="fas fa-flask"></i> Учёный</button>
        </div>
        
        <div class="card" style="background: rgba(151, 117, 250, 0.1); border-color: var(--purple);">
            <h4><i class="fas fa-crown"></i> PRO Подписка</h4>
            <p>{PRO_PRICE} руб. / {PRO_LIMIT} запросов в день</p>
            <input type="text" id="proCode" placeholder="Код активации" style="width: 100%; padding: 10px; margin: 10px 0;">
            <button class="btn" onclick="activatePro()" style="width: 100%; background: var(--purple);">
                <i class="fas fa-bolt"></i> Активировать
            </button>
        </div>
    </div>
    '''
    
    content = f'''
    <div class="card">
        <h3>Чат с Mateus AI</h3>
        <div id="chatMessages" class="chat-messages">
            <div class="ai-message">
                <strong>🤖 Mateus AI</strong><br>
                Привет! Я ваш AI помощник. Задавайте вопросы!
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Введите сообщение...">
            <button class="btn btn-primary" onclick="sendMessage()">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
    </div>
    
    <script>
        function selectRole(role) {{
            fetch('/set_role', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{role: role}})
            }});
            alert('Роль "' + role + '" выбрана');
        }}
    </script>
    '''
    
    footer = f'''
    <div class="footer">
        <p>Mateus AI | Версия для Render.com</p>
        <p><a href="/admin" style="color: var(--accent);">Админ-панель</a></p>
    </div>
    '''
    
    return render_page('Mateus AI', header, sidebar, content, footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    data = request.get_json()
    role = data.get('role', 'assistant')
    session['current_role'] = role
    return jsonify({'success': True})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = get_user_id()
        
        can_request, limit, used = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': f'Лимит исчерпан ({used}/{limit}). Купите PRO!'
            })
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Пустое сообщение'})
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'OpenAI клиент не инициализирован. Проверьте API ключ.'
            })
        
        role = session.get('current_role', 'assistant')
        system_prompt = ROLES.get(role, ROLES['assistant'])
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            increment_request(user_id)
            
            return jsonify({'success': True, 'response': answer})
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Ошибка OpenAI: {str(e)}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/activate_pro', methods=['POST'])
def activate_pro():
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    
    user_id = get_user_id()
    
    if code in settings_db.get('pro_codes', {}):
        pro_data = settings_db['pro_codes'][code]
        
        if not pro_data.get('used'):
            user = users_db[user_id]
            user['is_pro'] = True
            user['pro_until'] = (datetime.now() + timedelta(days=30)).isoformat()
            user['limit'] = PRO_LIMIT
            
            pro_data['used'] = True
            pro_data['used_by'] = user_id
            pro_data['used_at'] = datetime.now().isoformat()
            
            if not os.environ.get('RENDER'):
                save_data(USERS_FILE, users_db)
                save_data(SETTINGS_FILE, settings_db)
            
            return jsonify({
                'success': True,
                'message': 'PRO активирован на 30 дней!'
            })
    
    return jsonify({'success': False, 'message': 'Неверный или использованный код'})

# Упрощенная админ-панель
@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return '''
        <div style="max-width: 400px; margin: 100px auto; padding: 30px; background: #162416; border-radius: 15px;">
            <h2>Вход в админку</h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Пароль" style="width: 100%; padding: 10px; margin: 10px 0;">
                <button type="submit" style="width: 100%; padding: 10px; background: #32cd32; border: none; border-radius: 5px; color: white;">
                    Войти
                </button>
            </form>
        </div>
        '''
    
    users_total = len(users_db)
    pro_users = sum(1 for u in users_db.values() if u.get('is_pro'))
    requests_today = sum(u.get('requests_today', 0) for u in users_db.values())
    
    return f'''
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
        <h1>Админ-панель</h1>
        <a href="/">На главную</a>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="background: #1a5d1a; padding: 20px; border-radius: 10px;">
                <h3>Пользователей</h3>
                <p style="font-size: 2rem;">{users_total}</p>
            </div>
            <div style="background: #9775fa; padding: 20px; border-radius: 10px;">
                <h3>PRO пользователей</h3>
                <p style="font-size: 2rem;">{pro_users}</p>
            </div>
            <div style="background: #2e8b57; padding: 20px; border-radius: 10px;">
                <h3>Запросов сегодня</h3>
                <p style="font-size: 2rem;">{requests_today}</p>
            </div>
        </div>
        
        <h2>Пользователи</h2>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #2a5c2a;">
                    <th style="padding: 10px; text-align: left;">ID</th>
                    <th style="padding: 10px; text-align: left;">PRO</th>
                    <th style="padding: 10px; text-align: left;">Запросы</th>
                    <th style="padding: 10px; text-align: left;">Действия</th>
                </tr>
                {"".join([f'''
                <tr style="border-bottom: 1px solid #2a5c2a;">
                    <td style="padding: 10px;">{user_id[:8]}...</td>
                    <td style="padding: 10px;">{"✅" if user.get('is_pro') else "❌"}</td>
                    <td style="padding: 10px;">{user.get('requests_today', 0)}</td>
                    <td style="padding: 10px;">
                        <button onclick="togglePro('{user_id}')" style="padding: 5px 10px; margin-right: 5px;">
                            {"❌ Снять PRO" if user.get('is_pro') else "✅ Дать PRO"}
                        </button>
                    </td>
                </tr>
                ''' for user_id, user in list(users_db.items())[:50]])}
            </table>
        </div>
        
        <h2 style="margin-top: 40px;">Создать PRO код</h2>
        <form id="createCodeForm" style="margin: 20px 0;">
            <input type="number" name="days" placeholder="Дней (30)" value="30" style="padding: 10px; margin-right: 10px;">
            <button type="button" onclick="createCode()" style="padding: 10px 20px; background: #ffd700; border: none; border-radius: 5px;">
                Создать код
            </button>
        </form>
        
        <script>
            function togglePro(userId) {{
                fetch(`/admin/toggle_pro/${{userId}}`, {{method: 'POST'}})
                    .then(() => location.reload());
            }}
            
            function createCode() {{
                const days = document.querySelector('input[name="days"]').value;
                fetch(`/admin/create_code?days=${{days}}&password={password}`, {{method: 'POST'}})
                    .then(r => r.json())
                    .then(data => {{
                        alert('Код создан: ' + data.code);
                        location.reload();
                    }});
            }}
        </script>
    </div>
    '''

@app.route('/admin/toggle_pro/<user_id>', methods=['POST'])
def admin_toggle_pro():
    # Простая реализация для демонстрации
    return jsonify({'success': True})

@app.route('/admin/create_code', methods=['POST'])
def create_pro_code():
    days = request.args.get('days', 30)
    password = request.args.get('password')
    
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False})
    
    code = f"PRO-{secrets.token_hex(4).upper()}"
    settings_db.setdefault('pro_codes', {})[code] = {
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=int(days))).isoformat(),
        'used': False
    }
    
    if not os.environ.get('RENDER'):
        save_data(SETTINGS_FILE, settings_db)
    
    return jsonify({'success': True, 'code': code})

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    
    print("=" * 60)
    print("🚀 Mateus AI - Запуск на Render.com")
    print("=" * 60)
    print(f"🔑 OpenAI API: {'✅ Настроен' if openai_api_key else '❌ Не настроен'}")
    print(f"🔐 Админ пароль: {'✅ Настроен' if ADMIN_PASSWORD else '⚠️  Используется default'}")
    print(f"🌐 Порт: {port}")
    print(f"🚀 Запуск...")
    print("=" * 60)
    
    # На Render.com используем порт из переменной окружения
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
