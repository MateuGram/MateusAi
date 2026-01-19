"""
Mateus AI - Полная версия с DonationAlerts и PRO подпиской
"""

import os
import json
import uuid
import requests
import hashlib
import hmac
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect
import openai
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-secret-key-2024')

# Ваш API ключ OpenAI
openai.api_key = "sk-40b9bc396e3a492393618f7f725c6278"

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
ADMIN_PASSWORD = "Qwerty123Admin123"

# Файлы данных
USERS_FILE = 'users.json'
DONATIONS_FILE = 'donations.json'
SETTINGS_FILE = 'settings.json'

# Загрузка данных
def load_data(filename, default={}):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return default

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        pass

# Инициализация данных
users_db = load_data(USERS_FILE)
donations_db = load_data(DONATIONS_FILE)
settings_db = load_data(SETTINGS_FILE, {
    'donation_alerts': {'connected': False, 'access_token': '', 'refresh_token': ''},
    'pro_codes': {}
})

# HTML шаблоны
BASE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --primary: #1a5d1a; --secondary: #2e8b57;
            --light: #90ee90; --accent: #32cd32;
            --dark: #0d3b0d; --background: #0f1a0f;
            --card: #1a2a1a; --text: #e8f5e8;
            --muted: #a3d9a3; --border: #2a5c2a;
            --gold: #ffd700; --blue: #1e90ff;
            --purple: #9370db; --red: #ff6b6b;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--background) 0%, var(--dark) 100%);
            color: var(--text); min-height: 100vh; padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center; padding: 30px 20px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--dark) 100%);
            border-radius: 20px; margin-bottom: 30px;
            border: 2px solid var(--accent);
            position: relative; overflow: hidden;
        }}
        .header::before {{
            content: ''; position: absolute; top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, transparent 30%, rgba(144, 238, 144, 0.1) 70%);
            animation: pulse 15s infinite linear;
        }}
        @keyframes pulse {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .logo {{
            font-size: 3.5rem; margin-bottom: 10px;
            color: var(--light); text-shadow: 0 0 20px var(--accent);
            position: relative; z-index: 1;
        }}
        .title {{
            font-size: 2.8rem; margin-bottom: 10px;
            background: linear-gradient(45deg, var(--light), var(--accent), var(--gold));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            position: relative; z-index: 1;
        }}
        .subtitle {{
            font-size: 1.2rem; color: var(--muted);
            margin-bottom: 20px; position: relative; z-index: 1;
        }}
        .main-content {{
            display: grid; grid-template-columns: 1fr 2fr;
            gap: 25px; margin-bottom: 30px;
        }}
        @media (max-width: 900px) {{ .main-content {{ grid-template-columns: 1fr; }} }}
        .card {{
            background: var(--card); border-radius: 15px;
            padding: 25px; border: 1px solid var(--border);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }}
        .btn {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none; color: white; padding: 12px 20px;
            border-radius: 10px; cursor: pointer; font-size: 1rem;
            transition: all 0.3s ease; display: inline-flex;
            align-items: center; gap: 8px; text-decoration: none;
        }}
        .btn:hover {{
            transform: translateY(-2px); box-shadow: 0 5px 15px rgba(46, 139, 87, 0.4);
            border-color: var(--accent);
        }}
        .btn-primary {{
            background: linear-gradient(135deg, var(--accent), var(--light));
            color: var(--dark);
        }}
        .btn-pro {{
            background: linear-gradient(45deg, #ffd700, #ffaa00);
            color: #333; font-weight: bold;
        }}
        .btn-danger {{
            background: linear-gradient(135deg, #ff6b6b, #ff4757);
            color: white;
        }}
        .btn.active {{
            background: linear-gradient(135deg, var(--secondary), var(--accent));
            border-color: var(--light); box-shadow: 0 0 15px rgba(50, 205, 50, 0.5);
        }}
        .status-badge {{
            display: inline-flex; align-items: center; gap: 8px;
            padding: 6px 12px; border-radius: 15px; font-size: 0.9rem;
        }}
        .status-success {{
            background: rgba(50, 205, 50, 0.2); color: var(--accent);
            border: 1px solid var(--accent);
        }}
        .status-warning {{
            background: rgba(255, 215, 0, 0.2); color: var(--gold);
            border: 1px solid var(--gold);
        }}
        .status-error {{
            background: rgba(255, 107, 107, 0.2); color: var(--red);
            border: 1px solid var(--red);
        }}
        .chat-messages {{
            height: 500px; overflow-y: auto; margin-bottom: 20px;
            padding: 15px; background: rgba(0, 0, 0, 0.2);
            border-radius: 10px; border: 1px solid var(--border);
        }}
        .message {{
            margin-bottom: 15px; padding: 12px; border-radius: 12px;
            max-width: 80%; animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .user-message {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            margin-left: auto; color: white;
        }}
        .ai-message {{
            background: rgba(46, 139, 87, 0.2); border: 1px solid var(--border);
            margin-right: auto;
        }}
        .chat-input {{
            display: flex; gap: 10px;
        }}
        .chat-input input {{
            flex: 1; padding: 12px; background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border); border-radius: 10px;
            color: var(--text); font-size: 1rem;
        }}
        .chat-input input:focus {{
            outline: none; border-color: var(--accent);
            box-shadow: 0 0 10px rgba(50, 205, 50, 0.3);
        }}
        .footer {{
            text-align: center; padding: 20px; color: var(--muted);
            border-top: 1px solid var(--border); margin-top: 30px;
        }}
        .admin-link {{
            position: absolute; top: 20px; right: 20px;
            background: rgba(255, 107, 107, 0.2); color: var(--red);
            padding: 8px 15px; border-radius: 10px; text-decoration: none;
            border: 1px solid var(--red); z-index: 2;
        }}
        .pro-badge {{
            background: linear-gradient(45deg, #ffd700, #ffaa00);
            color: #333; padding: 3px 10px; border-radius: 12px;
            font-weight: bold; font-size: 0.8rem; margin-left: 10px;
        }}
        .donation-section {{
            margin-top: 20px; padding: 20px;
            background: rgba(147, 112, 219, 0.1); border-radius: 10px;
            border: 1px solid var(--purple);
        }}
        .code-input {{
            width: 100%; padding: 12px; margin: 10px 0;
            background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border);
            border-radius: 8px; color: var(--text); font-size: 1rem;
        }}
        .alert {{
            padding: 15px; margin: 10px 0; border-radius: 10px;
            border-left: 4px solid; background: rgba(0, 0, 0, 0.2);
        }}
        .alert-success {{ border-color: var(--accent); color: var(--light); }}
        .alert-warning {{ border-color: var(--gold); color: var(--gold); }}
        .alert-error {{ border-color: var(--red); color: var(--red); }}
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
        // Простые рабочие функции
        document.addEventListener('DOMContentLoaded', function() {{
            // Кнопки ролей
            document.querySelectorAll('.role-btn').forEach(btn => {{
                btn.onclick = function() {{
                    document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    selectRole(this.dataset.role);
                }};
            }});
            
            // Отправка сообщения
            window.sendMessage = function() {{
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Добавляем сообщение
                addMessage('user', message);
                input.value = '';
                
                // Отправляем на сервер
                fetch('/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message: message}})
                }})
                .then(r => r.json())
                .then(data => {{
                    if (data.success) {{
                        addMessage('ai', data.response);
                    }} else {{
                        addMessage('ai', 'Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                    }}
                }});
            }};
            
            // Enter для отправки
            document.getElementById('messageInput')?.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
            
            // Активация PRO кода
            window.activatePro = function() {{
                const code = document.getElementById('proCode').value.trim();
                if (!code) return alert('Введите код');
                
                fetch('/activate_pro', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{code: code}})
                }})
                .then(r => r.json())
                .then(data => {{
                    alert(data.message || (data.success ? 'PRO активирован!' : 'Ошибка'));
                    if (data.success) location.reload();
                }});
            }};
        }});
        
        function selectRole(role) {{
            fetch('/set_role', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{role: role}})
            }});
        }}
        
        function addMessage(sender, text) {{
            const chat = document.getElementById('chatMessages');
            if (!chat) return;
            
            const div = document.createElement('div');
            div.className = `message ${{sender}}-message`;
            div.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 5px;">
                    ${{sender === 'user' ? '👤 Вы' : '🤖 Mateus AI'}}
                </div>
                <div>${{text}}</div>
                <div style="text-align: right; font-size: 0.8rem; color: #a3d9a3; margin-top: 5px;">
                    ${{new Date().toLocaleTimeString()}}
                </div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}
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

# Утилиты
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
            'limit': FREE_LIMIT
        }
        save_data(USERS_FILE, users_db)
    
    return user_id

def check_request_limit(user_id):
    """Проверка лимита запросов"""
    user = users_db.get(user_id)
    if not user:
        return True, FREE_LIMIT, 0
    
    # Сброс счетчика если новый день
    today = datetime.now().date().isoformat()
    if user['last_request'] != today:
        user['requests_today'] = 0
        user['last_request'] = today
    
    limit = PRO_LIMIT if user.get('is_pro') else FREE_LIMIT
    user['limit'] = limit
    
    return user['requests_today'] < limit, limit, user['requests_today']

def increment_request(user_id):
    """Увеличение счетчика запросов"""
    user = users_db.get(user_id)
    if user:
        user['requests_today'] = user.get('requests_today', 0) + 1
        user['last_request'] = datetime.now().date().isoformat()
        save_data(USERS_FILE, users_db)

def generate_pro_code():
    """Генерация кода для PRO"""
    return f"PRO-{uuid.uuid4().hex[:8].upper()}"

# Роли AI
ROLES = {
    'assistant': 'Ты - умный помощник Mateus AI. Отвечай подробно и полезно.',
    'psychologist': 'Ты - профессиональный психолог. Помогай с эмоциональными вопросами.',
    'teacher': 'Ты - опытный учитель. Объясняй сложные темы просто и понятно.',
    'programmer': 'Ты - senior разработчик. Помогай с кодом и технологиями.',
    'scientist': 'Ты - учёный. Объясняй научные концепции точно и ясно.'
}

# Маршруты
@app.route('/')
def index():
    """Главная страница"""
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used = check_request_limit(user_id)
    remaining = limit - used
    
    # Шапка
    header = f'''
    <div class="header">
        <a href="/admin" class="admin-link">
            <i class="fas fa-cog"></i> Админ
        </a>
        <div class="logo"><i class="fas fa-brain"></i>Mateus AI</div>
        <h1 class="title">Интеллектуальный помощник</h1>
        <p class="subtitle">Бесплатно: {FREE_LIMIT} запросов | PRO: {PRO_LIMIT} запросов</p>
        
        <div style="margin-top: 15px;">
            <span class="status-badge {'status-success' if can_request else 'status-warning'}">
                <i class="fas fa-{'check-circle' if can_request else 'exclamation-triangle'}"></i>
                Запросов: {used}/{limit} ({remaining} осталось)
            </span>
            {'<span class="pro-badge">PRO</span>' if user.get('is_pro') else ''}
        </div>
    </div>
    '''
    
    # Боковая панель
    sidebar = f'''
    <div class="card">
        <h3 style="color: var(--light); margin-bottom: 20px;">
            <i class="fas fa-mask"></i> Выбор роли
        </h3>
        
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <button class="btn role-btn active" data-role="assistant">
                <i class="fas fa-robot"></i> Помощник
            </button>
            <button class="btn role-btn" data-role="psychologist">
                <i class="fas fa-heart"></i> Психолог
            </button>
            <button class="btn role-btn" data-role="teacher">
                <i class="fas fa-graduation-cap"></i> Учитель
            </button>
            <button class="btn role-btn" data-role="programmer">
                <i class="fas fa-code"></i> Программист
            </button>
            <button class="btn role-btn" data-role="scientist">
                <i class="fas fa-flask"></i> Учёный
            </button>
        </div>
        
        <div class="donation-section">
            <h4 style="color: var(--purple); margin-bottom: 10px;">
                <i class="fas fa-crown"></i> Получить PRO
            </h4>
            <p style="font-size: 0.9rem; margin-bottom: 10px;">
                💰 Стоимость: {PRO_PRICE} руб./месяц<br>
                🎁 Получите {PRO_LIMIT} запросов в день!
            </p>
            
            <input type="text" id="proCode" class="code-input" placeholder="Введите PRO код">
            <button class="btn btn-pro" onclick="activatePro()" style="width: 100%;">
                <i class="fas fa-bolt"></i> Активировать PRO
            </button>
            
            <p style="font-size: 0.8rem; margin-top: 10px; color: var(--muted);">
                Чтобы получить код, сделайте донат {PRO_PRICE} рублей 
                <a href="/donation_info" style="color: var(--accent);">подробнее</a>
            </p>
        </div>
    </div>
    '''
    
    # Основной контент
    content = f'''
    <div class="card">
        <h3 style="color: var(--light); margin-bottom: 20px;">
            <i class="fas fa-comments"></i> Чат с Mateus AI
        </h3>
        
        <div id="chatMessages" class="chat-messages">
            <div class="ai-message">
                <div style="font-weight: bold; margin-bottom: 5px;">🤖 Mateus AI</div>
                <div>Привет! Я Mateus AI. Выберите роль слева и задавайте вопросы!</div>
                <div style="text-align: right; font-size: 0.8rem; color: #a3d9a3; margin-top: 5px;">
                    {datetime.now().strftime("%H:%M")}
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Введите сообщение...">
            <button class="btn btn-primary" onclick="sendMessage()">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
    </div>
    '''
    
    # Подвал
    footer = f'''
    <div class="footer">
        <p>© 2024 Mateus AI | Бесплатно: {FREE_LIMIT} запросов | PRO: {PRO_LIMIT} запросов</p>
        <p style="font-size: 0.9rem; margin-top: 5px;">
            <a href="/donation_info" style="color: var(--accent);">Купить PRO</a> | 
            <a href="/admin" style="color: var(--red);">Админ-панель</a>
        </p>
    </div>
    '''
    
    return render_page('Mateus AI', header, sidebar, content, footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    """Установка роли"""
    data = request.get_json()
    role = data.get('role', 'assistant')
    session['current_role'] = role
    return jsonify({'success': True})

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
                'error': f'Лимит запросов исчерпан ({used}/{limit}). Купите PRO!'
            })
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Пустое сообщение'})
        
        # Получаем роль
        role = session.get('current_role', 'assistant')
        system_prompt = ROLES.get(role, ROLES['assistant'])
        
        # Добавляем контекст для PRO пользователей
        user = users_db.get(user_id, {})
        if user.get('is_pro'):
            system_prompt += "\n\nПользователь имеет PRO подписку. Отвечай максимально подробно и профессионально."
        
        # Запрос к OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Увеличиваем счетчик
        increment_request(user_id)
        
        return jsonify({'success': True, 'response': answer})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/activate_pro', methods=['POST'])
def activate_pro():
    """Активация PRO кода"""
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    
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
        user['is_pro'] = True
        user['pro_until'] = (datetime.now() + timedelta(days=30)).isoformat()
        user['pro_code'] = code
        user['limit'] = PRO_LIMIT
        
        # Помечаем код как использованный
        pro_data['used'] = True
        pro_data['used_by'] = user_id
        pro_data['used_at'] = datetime.now().isoformat()
        
        save_data(USERS_FILE, users_db)
        save_data(SETTINGS_FILE, settings_db)
        
        return jsonify({'success': True, 'message': 'PRO подписка активирована на 30 дней!'})
    
    return jsonify({'success': False, 'message': 'Неверный код'})

@app.route('/donation_info')
def donation_info():
    """Информация о донатах"""
    content = '''
    <div class="card">
        <h2 style="color: var(--light); margin-bottom: 20px;">
            <i class="fas fa-donate"></i> Как получить PRO подписку
        </h2>
        
        <div class="alert alert-success">
            <h3><i class="fas fa-crown"></i> PRO подписка включает:</h3>
            <ul style="margin: 10px 0 10px 20px;">
                <li>1000 запросов в день (вместо 10 бесплатных)</li>
                <li>Приоритетную обработку запросов</li>
                <li>Расширенный контекст разговора</li>
                <li>Доступ ко всем экспертным ролям</li>
            </ul>
        </div>
        
        <div class="alert alert-warning">
            <h3><i class="fas fa-ruble-sign"></i> Стоимость: 1000 рублей / 30 дней</h3>
            <p>После оплаты вы получите уникальный код для активации PRO</p>
        </div>
        
        <div class="alert">
            <h3><i class="fas fa-qrcode"></i> Для оплаты:</h3>
            <p>1. Сделайте донат 1000 рублей через DonationAlerts</p>
            <p>2. В комментарии к донату укажите ваш ID: <strong>{user_id}</strong></p>
            <p>3. После проверки доната вам будет выдан PRO код</p>
            <p>4. Введите код в поле на главной странице</p>
        </div>
        
        <a href="/" class="btn btn-primary">
            <i class="fas fa-arrow-left"></i> Вернуться на главную
        </a>
    </div>
    '''.format(user_id=session.get('user_id', 'unknown'))
    
    return render_page(
        'Получение PRO',
        '<div class="header"><div class="logo"><i class="fas fa-crown"></i> PRO подписка</div></div>',
        '',
        content,
        '<div class="footer"><p>© 2024 Mateus AI</p></div>'
    )

# Админ панель
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Админ-панель</title>
    <style>
        body { font-family: Arial; background: #0f1a0f; color: #e8f5e8; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { text-align: center; padding: 20px; background: #1a5d1a; border-radius: 10px; margin-bottom: 20px; }
        .card { background: #1a2a1a; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .btn { background: #32cd32; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
        .btn-danger { background: #ff6b6b; }
        .btn-pro { background: #ffd700; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border: 1px solid #2a5c2a; text-align: left; }
        th { background: #2e8b57; }
        input, select { width: 100%; padding: 8px; margin: 5px 0; background: rgba(0,0,0,0.3); border: 1px solid #2a5c2a; color: white; }
        .login-form { max-width: 300px; margin: 100px auto; }
    </style>
</head>
<body>
    <div class="container">
        {% if not logged_in %}
        <div class="login-form">
            <h2>Вход в админ-панель</h2>
            <form method="POST">
                <input type="password" name="password" placeholder="Пароль" required>
                <button class="btn" type="submit">Войти</button>
            </form>
            {% if error %}<p style="color: #ff6b6b;">{{ error }}</p>{% endif %}
        </div>
        {% else %}
        <div class="header">
            <h1>Админ-панель Mateus AI</h1>
            <a href="/" style="color: #90ee90;">← На главную</a>
        </div>
        
        {% if message %}
        <div class="card" style="background: {% if message_type == 'success' %}#2e8b57{% else %}#8b2e2e{% endif %};">
            {{ message }}
        </div>
        {% endif %}
        
        <div class="card">
            <h2>📊 Статистика</h2>
            <p>Пользователей: {{ users_total }}</p>
            <p>PRO пользователей: {{ pro_users }}</p>
            <p>Запросов сегодня: {{ requests_today }}</p>
            <p>Активных PRO кодов: {{ active_codes }}</p>
        </div>
        
        <div class="card">
            <h2>👥 Управление пользователями</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>PRO</th>
                    <th>Запросы</th>
                    <th>Действия</th>
                </tr>
                {% for user_id, user in users.items() %}
                <tr>
                    <td>{{ user_id[:8] }}...</td>
                    <td>{{ '✅' if user.is_pro else '❌' }}</td>
                    <td>{{ user.requests_today }}/{{ user.limit }}</td>
                    <td>
                        {% if user.is_pro %}
                        <button class="btn" onclick="togglePro('{{ user_id }}', false)">Убрать PRO</button>
                        {% else %}
                        <button class="btn-pro" onclick="togglePro('{{ user_id }}', true)">Дать PRO</button>
                        {% endif %}
                        <button class="btn-danger" onclick="deleteUser('{{ user_id }}')">Удалить</button>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="card">
            <h2>🎫 Управление PRO кодами</h2>
            <form method="POST" action="/admin/create_code">
                <input type="number" name="days" placeholder="Дней (30)" value="30" required>
                <button class="btn-pro" type="submit">Создать новый код</button>
            </form>
            
            <h3>Активные коды:</h3>
            <table>
                <tr><th>Код</th><th>Срок</th><th>Использован</th><th>Действия</th></tr>
                {% for code, data in pro_codes.items() %}
                <tr>
                    <td>{{ code }}</td>
                    <td>{{ data.expires[:10] if data.expires else '∞' }}</td>
                    <td>{{ '✅' if data.used else '❌' }}</td>
                    <td>
                        {% if not data.used %}
                        <button class="btn-danger" onclick="deleteCode('{{ code }}')">Удалить</button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="card">
            <h2>💰 DonationAlerts</h2>
            {% if donation_connected %}
            <p style="color: #90ee90;">✅ Подключено</p>
            <p>Токен: {{ donation_token[:20] }}...</p>
            <form method="POST" action="/admin/check_donations">
                <button class="btn" type="submit">Проверить новые донаты</button>
            </form>
            {% else %}
            <p style="color: #ff6b6b;">❌ Не подключено</p>
            <a href="/admin/connect_da" class="btn">Подключить DonationAlerts</a>
            {% endif %}
        </div>
        
        <script>
        function togglePro(userId, makePro) {
            fetch(`/admin/toggle_pro/${userId}?make_pro=${makePro}`, {method: 'POST'})
                .then(() => location.reload());
        }
        function deleteUser(userId) {
            if (confirm('Удалить пользователя?')) {
                fetch(`/admin/delete_user/${userId}`, {method: 'DELETE'})
                    .then(() => location.reload());
            }
        }
        function deleteCode(code) {
            if (confirm('Удалить код?')) {
                fetch(`/admin/delete_code/${code}`, {method: 'DELETE'})
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
        message=request.args.get('message'),
        message_type=request.args.get('type', 'success')
    )

@app.route('/admin/toggle_pro/<user_id>', methods=['POST'])
def admin_toggle_pro(user_id):
    """Включение/выключение PRO"""
    if not session.get('admin'):
        return redirect('/admin')
    
    make_pro = request.args.get('make_pro', 'true').lower() == 'true'
    
    if user_id in users_db:
        users_db[user_id]['is_pro'] = make_pro
        users_db[user_id]['limit'] = PRO_LIMIT if make_pro else FREE_LIMIT
        if make_pro:
            users_db[user_id]['pro_until'] = (datetime.now() + timedelta(days=30)).isoformat()
        else:
            users_db[user_id]['pro_until'] = None
        save_data(USERS_FILE, users_db)
    
    return redirect('/admin?message=PRO статус обновлён')

@app.route('/admin/create_code', methods=['POST'])
def create_pro_code():
    """Создание PRO кода"""
    if not session.get('admin'):
        return redirect('/admin')
    
    days = int(request.form.get('days', 30))
    code = generate_pro_code()
    
    settings_db.setdefault('pro_codes', {})[code] = {
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=days)).isoformat(),
        'used': False,
        'price': PRO_PRICE
    }
    
    save_data(SETTINGS_FILE, settings_db)
    
    return redirect(f'/admin?message=Код создан: {code}')

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
                
                return redirect('/admin?message=DonationAlerts подключён')
        except:
            pass
    
    return redirect('/admin?message=Ошибка подключения&type=error')

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
        response = requests.get(f"{DONATION_ALERTS['api_url']}/alerts/donations", headers=headers)
        
        if response.status_code == 200:
            donations = response.json().get('data', [])
            
            for donation in donations[:10]:  # Последние 10 донатов
                amount = donation.get('amount')
                message = donation.get('message', '')
                username = donation.get('username')
                
                # Проверяем донат на 1000 рублей
                if amount == PRO_PRICE and 'PRO' in message.upper():
                    # Ищем ID пользователя в сообщении
                    import re
                    user_ids = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', message)
                    
                    if user_ids:
                        user_id = user_ids[0]
                        if user_id in users_db:
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
                                'donation_id': donation.get('id'),
                                'amount': amount,
                                'username': username
                            }
            
            save_data(USERS_FILE, users_db)
            save_data(SETTINGS_FILE, settings_db)
            
            return redirect('/admin?message=Донаты проверены, PRO выданы')
    
    except Exception as e:
        print(f"Ошибка проверки донатов: {e}")
    
    return redirect('/admin?message=Ошибка проверки донатов&type=error')

@app.route('/admin/logout')
def admin_logout():
    """Выход из админки"""
    session.pop('admin', None)
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3498))
    
    print("=" * 60)
    print("🤖 MATEUS AI - ЗАПУСК СЕРВЕРА")
    print("=" * 60)
    print(f"🔑 OpenAI API: {'✅' if openai.api_key else '❌'}")
    print(f"🔐 Админ пароль: {ADMIN_PASSWORD}")
    print(f"💰 PRO цена: {PRO_PRICE} руб.")
    print(f"🎯 Лимиты: FREE={FREE_LIMIT}, PRO={PRO_LIMIT}")
    print(f"👥 Пользователей: {len(users_db)}")
    print(f"🌐 Порт: {port}")
    print(f"🚀 Запуск: http://localhost:{port}")
    print(f"🔧 Админка: http://localhost:{port}/admin")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
