"""
Mateus AI - Полная версия с OpenAI и PRO подпиской для Render.com
"""

import os
import json
import uuid
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== КОНФИГУРАЦИЯ ====================

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️  OpenAI API Key not found. Some features will be limited.")
    client = None
else:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ OpenAI init error: {e}")
        client = None

# Лимиты
FREE_LIMIT = 10
PRO_LIMIT = 1000
PRO_PRICE = 1000

# Пароль админа
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123")

# ==================== ХРАНЕНИЕ ДАННЫХ ====================

# Временное хранилище в памяти
users_db = {}
settings_db = {
    'donation_alerts': {'connected': False, 'access_token': '', 'refresh_token': ''},
    'pro_codes': {}
}
donations_db = {}

# ==================== HTML ШАБЛОНЫ ====================

BASE_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #1a5d1a; --secondary: #2e8b57; --light: #90ee90;
            --accent: #32cd32; --dark: #0d3b0d; --background: #0a1a0a;
            --card: #162416; --text: #f0fff0; --muted: #a3d9a3;
            --border: #2a5c2a; --gold: #ffd700; --blue: #4dabf7;
            --purple: #9775fa; --red: #ff6b6b; --pink: #f783ac;
        }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: var(--background);
            color: var(--text);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center; padding: 40px 30px;
            background: linear-gradient(135deg, var(--primary), var(--dark));
            border-radius: 20px; margin-bottom: 40px;
            border: 2px solid var(--accent);
            position: relative; overflow: hidden;
        }}
        .logo {{ font-size: 3.5rem; color: var(--light); margin-bottom: 10px; }}
        .title {{ font-size: 3rem; background: linear-gradient(45deg, var(--light), var(--accent));
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 15px; }}
        .main-content {{ display: grid; grid-template-columns: 1fr 3fr; gap: 30px; }}
        @media (max-width: 1100px) {{ .main-content {{ grid-template-columns: 1fr; }} }}
        .card {{
            background: var(--card); border-radius: 15px;
            padding: 30px; border: 1px solid var(--border);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}
        .btn {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none; color: white; padding: 12px 24px;
            border-radius: 10px; cursor: pointer; font-size: 1rem;
            transition: all 0.3s; display: inline-flex;
            align-items: center; gap: 10px; text-decoration: none;
        }}
        .btn:hover {{ transform: translateY(-3px); box-shadow: 0 10px 25px rgba(46,139,87,0.4); }}
        .btn-primary {{ background: linear-gradient(135deg, var(--accent), var(--light)); color: var(--dark); }}
        .btn-pro {{ background: linear-gradient(45deg, #ffd700, #ffaa00); color: #333; font-weight: bold; }}
        .btn-danger {{ background: linear-gradient(135deg, var(--red), #ff4757); color: white; }}
        .chat-messages {{
            height: 500px; overflow-y: auto; margin-bottom: 25px;
            padding: 20px; background: rgba(0,0,0,0.2);
            border-radius: 10px; border: 1px solid var(--border);
        }}
        .message {{
            margin-bottom: 20px; padding: 15px; border-radius: 12px;
            max-width: 85%; animation: fadeIn 0.3s;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .user-message {{ background: linear-gradient(135deg, var(--primary), var(--secondary)); margin-left: auto; color: white; }}
        .ai-message {{ background: rgba(46,139,87,0.2); border: 1px solid var(--border); margin-right: auto; }}
        .chat-input {{ display: flex; gap: 15px; }}
        .chat-input input {{
            flex: 1; padding: 15px; background: rgba(0,0,0,0.3);
            border: 1px solid var(--border); border-radius: 10px;
            color: var(--text); font-size: 1rem;
        }}
        .chat-input input:focus {{ outline: none; border-color: var(--accent); box-shadow: 0 0 10px rgba(50,205,50,0.3); }}
        .footer {{ text-align: center; padding: 30px; color: var(--muted);
                 border-top: 1px solid var(--border); margin-top: 40px; }}
        .roles-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; margin: 20px 0; }}
        .role-card {{
            background: rgba(22,36,22,0.6); border: 1px solid var(--border);
            border-radius: 10px; padding: 20px; text-align: center;
            cursor: pointer; transition: all 0.3s;
        }}
        .role-card:hover {{ background: rgba(46,139,87,0.2); transform: translateY(-3px); }}
        .role-card.active {{ background: rgba(46,139,87,0.3); border-color: var(--accent); }}
        .status-badge {{
            display: inline-flex; align-items: center; gap: 8px;
            padding: 8px 16px; border-radius: 20px; font-size: 0.9rem;
            background: rgba(50,205,50,0.15); color: var(--accent);
            border: 1px solid rgba(50,205,50,0.3);
        }}
        .alert {{
            padding: 15px; margin: 15px 0; border-radius: 10px;
            border-left: 4px solid; background: rgba(0,0,0,0.2);
        }}
        .alert-success {{ border-color: var(--accent); }}
        .alert-error {{ border-color: var(--red); }}
        .pro-section {{
            margin-top: 30px; padding: 25px;
            background: rgba(151,117,250,0.1); border-radius: 15px;
            border: 1px solid var(--purple);
        }}
        .pro-badge {{
            background: linear-gradient(45deg, #ffd700, #ffaa00);
            color: #333; padding: 4px 12px; border-radius: 20px;
            font-weight: bold; font-size: 0.8rem; margin-left: 10px;
        }}
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
        document.addEventListener('DOMContentLoaded', function() {{
            // Роли
            document.querySelectorAll('.role-card').forEach(card => {{
                card.onclick = function() {{
                    document.querySelectorAll('.role-card').forEach(c => c.classList.remove('active'));
                    this.classList.add('active');
                    selectRole(this.dataset.role);
                }};
            }});
            
            // Отправка сообщений
            window.sendMessage = function() {{
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                const btn = document.querySelector('.chat-input .btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                btn.disabled = true;
                
                addMessage('user', message);
                input.value = '';
                
                fetch('/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message: message}})
                }})
                .then(r => r.json())
                .then(data => {{
                    if (data.success) {{
                        addMessage('ai', data.response);
                        updateUsage(data.usage);
                    }} else {{
                        addMessage('ai', '<div class="alert alert-error">' + data.error + '</div>');
                    }}
                }})
                .catch(error => {{
                    addMessage('ai', '<div class="alert alert-error">Ошибка сети</div>');
                }})
                .finally(() => {{
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    input.focus();
                }});
            }};
            
            // Enter для отправки
            document.getElementById('messageInput')?.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
            
            // PRO активация
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
                    alert(data.message);
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
                <div style="font-weight: bold; margin-bottom: 8px;">
                    ${{sender === 'user' ? '👤 Вы' : '🤖 Mateus AI'}}
                </div>
                <div>${{text}}</div>
                <div style="text-align: right; font-size: 0.8rem; color: var(--muted); margin-top: 5px;">
                    ${{new Date().toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}}
                </div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }}
        
        function updateUsage(usage) {{
            if (usage && document.getElementById('usageInfo')) {{
                document.getElementById('usageInfo').innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                        <span>Использовано: ${{usage.used}}/${{usage.limit}}</span>
                        <span>Осталось: ${{usage.remaining}}</span>
                    </div>
                `;
            }}
        }}
    </script>
</body>
</html>'''

def render_page(title, header, sidebar, content, footer):
    return render_template_string(BASE_HTML, title=title, header=header, sidebar=sidebar, content=content, footer=footer)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

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
            'pro_code': None,
            'limit': FREE_LIMIT,
            'total_requests': 0,
            'role': 'assistant'
        }
    
    return user_id

def check_request_limit(user_id):
    user = users_db.get(user_id, {})
    today = datetime.now().date().isoformat()
    
    if user.get('last_request') != today:
        user['requests_today'] = 0
        user['last_request'] = today
    
    limit = PRO_LIMIT if user.get('is_pro') else FREE_LIMIT
    user['limit'] = limit
    used = user.get('requests_today', 0)
    
    return used < limit, limit, used, limit - used

def increment_request(user_id):
    user = users_db.get(user_id)
    if user:
        user['requests_today'] = user.get('requests_today', 0) + 1
        user['total_requests'] = user.get('total_requests', 0) + 1
        user['last_request'] = datetime.now().date().isoformat()

def generate_pro_code():
    return f"PRO-{secrets.token_hex(4).upper()}"

# Роли AI
ROLES = {
    'assistant': {
        'name': 'Помощник',
        'prompt': 'Ты - умный помощник Mateus AI. Отвечай подробно и полезно.',
        'icon': 'fas fa-robot',
        'color': '#32cd32'
    },
    'psychologist': {
        'name': 'Психолог',
        'prompt': 'Ты - опытный психолог с эмпатией. Помогай с эмоциональными вопросами.',
        'icon': 'fas fa-heart',
        'color': '#ff6b6b'
    },
    'teacher': {
        'name': 'Учитель',
        'prompt': 'Ты - терпеливый учитель. Объясняй сложные темы простыми словами.',
        'icon': 'fas fa-graduation-cap',
        'color': '#4dabf7'
    },
    'programmer': {
        'name': 'Программист',
        'prompt': 'Ты - senior разработчик. Помогай с кодом и технологиями.',
        'icon': 'fas fa-code',
        'color': '#9775fa'
    },
    'scientist': {
        'name': 'Учёный',
        'prompt': 'Ты - учёный. Объясняй научные концепции точно и ясно.',
        'icon': 'fas fa-flask',
        'color': '#ffd700'
    }
}

# ==================== ОСНОВНЫЕ МАРШРУТЫ ====================

@app.route('/')
def index():
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used, remaining = check_request_limit(user_id)
    current_role = session.get('current_role', 'assistant')
    role_info = ROLES.get(current_role, ROLES['assistant'])
    
    header = f'''
    <div class="header">
        <a href="/admin" class="btn" style="position: absolute; top: 20px; right: 20px;">
            <i class="fas fa-cog"></i> Админ
        </a>
        <div class="logo"><i class="fas fa-brain"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p>Интеллектуальный помощник нового поколения</p>
        
        <div style="margin-top: 20px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
            <span class="status-badge">
                <i class="fas fa-{'rocket' if can_request else 'hourglass-end'}"></i>
                {used}/{limit} запросов
            </span>
            <span class="status-badge">
                <i class="{role_info['icon']}"></i>
                {role_info['name']}
            </span>
            {'<span class="pro-badge"><i class="fas fa-crown"></i> PRO</span>' if user.get('is_pro') else ''}
        </div>
        
        <div id="usageInfo" style="max-width: 600px; margin: 20px auto 0;">
            <div style="display: flex; justify-content: space-between;">
                <span>Использовано: <strong>{used}/{limit}</strong></span>
                <span>Осталось: <strong>{remaining}</strong></span>
            </div>
        </div>
    </div>
    '''
    
    sidebar = f'''
    <div class="card">
        <h3><i class="fas fa-mask"></i> Выбор роли</h3>
        <p style="color: var(--muted); margin-bottom: 20px;">Каждая роль имеет уникальный стиль</p>
        
        <div class="roles-grid">
            {''.join([f'''
            <div class="role-card {'active' if role_id == current_role else ''}" 
                 data-role="{role_id}">
                <div style="font-size: 1.5rem; color: {role_data['color']}; margin-bottom: 10px;">
                    <i class="{role_data['icon']}"></i>
                </div>
                <div style="font-weight: 600;">{role_data['name']}</div>
            </div>
            ''' for role_id, role_data in ROLES.items()])}
        </div>
        
        <div class="pro-section">
            <h4><i class="fas fa-crown"></i> PRO Подписка</h4>
            <div style="margin: 15px 0;">
                <p><i class="fas fa-check" style="color: var(--accent);"></i> {PRO_LIMIT} запросов в день</p>
                <p><i class="fas fa-check" style="color: var(--accent);"></i> Приоритетная обработка</p>
                <p><i class="fas fa-check" style="color: var(--accent);"></i> Расширенный контекст</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 2rem; font-weight: bold; color: var(--gold);">
                    {PRO_PRICE} ₽
                </div>
                <div style="color: var(--muted);">/ 30 дней</div>
            </div>
            
            <input type="text" id="proCode" placeholder="Введите PRO код" 
                   style="width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid var(--border); background: rgba(0,0,0,0.2); color: white;">
            <button class="btn btn-pro" onclick="activatePro()" style="width: 100%;">
                <i class="fas fa-bolt"></i> Активировать PRO
            </button>
            
            <p style="text-align: center; margin-top: 15px; font-size: 0.9rem;">
                <a href="/donation_info" style="color: var(--purple); text-decoration: none;">
                    <i class="fas fa-donate"></i> Как получить код?
                </a>
            </p>
        </div>
    </div>
    '''
    
    content = f'''
    <div class="card">
        <h3><i class="fas fa-comments"></i> Чат с Mateus AI</h3>
        
        <div id="chatMessages" class="chat-messages">
            <div class="ai-message">
                <strong>🤖 Mateus AI</strong>
                <div style="margin-top: 10px;">
                    <p>Привет! Я ваш AI помощник Mateus.</p>
                    <p>Я могу помочь с различными задачами:</p>
                    <ul style="margin: 10px 0 10px 20px;">
                        <li>Ответить на вопросы</li>
                        <li>Помочь с программированием</li>
                        <li>Объяснить сложные темы</li>
                        <li>Поддержать в трудную минуту</li>
                    </ul>
                    <p>Выберите роль слева для специализированной помощи!</p>
                </div>
                <div style="text-align: right; font-size: 0.8rem; color: var(--muted); margin-top: 10px;">
                    {datetime.now().strftime("%H:%M")}
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Введите ваш вопрос... (Enter для отправки)" autofocus>
            <button class="btn btn-primary" onclick="sendMessage()">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
        
        <div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap;">
            <button class="btn" onclick="document.getElementById('messageInput').value = 'Расскажи о своих возможностях'">
                <i class="fas fa-lightbulb"></i> Возможности
            </button>
            <button class="btn" onclick="document.getElementById('messageInput').value = 'Как работает AI?'">
                <i class="fas fa-robot"></i> Об AI
            </button>
            <button class="btn" onclick="document.getElementById('messageInput').value = 'Напиши пример кода на Python'">
                <i class="fas fa-code"></i> Код
            </button>
        </div>
    </div>
    '''
    
    footer = f'''
    <div class="footer">
        <p>© 2024 Mateus AI | Искусственный интеллект нового поколения</p>
        <div style="margin-top: 10px;">
            <a href="/donation_info" style="color: var(--accent); margin: 0 10px;">Получить PRO</a> • 
            <a href="/admin" style="color: var(--red); margin: 0 10px;">Админ-панель</a> • 
            <a href="/health" style="color: var(--blue); margin: 0 10px;">Статус</a>
        </div>
        <p style="margin-top: 10px; font-size: 0.9rem; color: var(--muted);">
            Бесплатно: {FREE_LIMIT} запросов/день | PRO: {PRO_LIMIT} запросов/день
        </p>
    </div>
    '''
    
    return render_page('Mateus AI - Умный помощник', header, sidebar, content, footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    data = request.get_json()
    role = data.get('role', 'assistant')
    
    if role in ROLES:
        session['current_role'] = role
        user_id = get_user_id()
        if user_id in users_db:
            users_db[user_id]['role'] = role
        
        return jsonify({
            'success': True,
            'role': role,
            'role_name': ROLES[role]['name']
        })
    
    return jsonify({'success': False, 'error': 'Неизвестная роль'})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = get_user_id()
        
        can_request, limit, used, remaining = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': f'Лимит запросов исчерпан ({used}/{limit}). Для увеличения лимита приобретите PRO подписку!'
            })
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})
        
        if not client:
            # Fallback ответ если OpenAI не настроен
            increment_request(user_id)
            _, new_limit, new_used, new_remaining = check_request_limit(user_id)
            
            fallback_responses = [
                f"Вы спросили: '{message}'. К сожалению, AI сервис временно недоступен. Пожалуйста, настройте OpenAI API ключ для полного функционала.",
                f"Вопрос: '{message}'. Для ответа на этот вопрос необходим доступ к AI сервису. Установите переменную OPENAI_API_KEY.",
                f"Спасибо за вопрос! Вы использовали {new_used} из {new_limit} запросов на сегодня."
            ]
            
            import random
            response = random.choice(fallback_responses)
            
            return jsonify({
                'success': True,
                'response': response,
                'usage': {
                    'used': new_used,
                    'limit': new_limit,
                    'remaining': new_remaining
                }
            })
        
        role = session.get('current_role', 'assistant')
        role_data = ROLES.get(role, ROLES['assistant'])
        system_prompt = role_data['prompt']
        
        user = users_db.get(user_id, {})
        if user.get('is_pro'):
            system_prompt += "\n\nПользователь имеет PRO подписку. Отвечай максимально подробно и профессионально."
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            increment_request(user_id)
            
            _, new_limit, new_used, new_remaining = check_request_limit(user_id)
            
            return jsonify({
                'success': True,
                'response': answer,
                'usage': {
                    'used': new_used,
                    'limit': new_limit,
                    'remaining': new_remaining
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Ошибка при обращении к AI: {str(e)}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка сервера: {str(e)}'})

@app.route('/activate_pro', methods=['POST'])
def activate_pro():
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return jsonify({'success': False, 'message': 'Введите код активации'})
        
        user_id = get_user_id()
        
        # Создаем тестовый код если нет кодов
        if not settings_db.get('pro_codes'):
            test_code = "PRO-TEST123"
            settings_db['pro_codes'] = {
                test_code: {
                    'created': datetime.now().isoformat(),
                    'expires': (datetime.now() + timedelta(days=365)).isoformat(),
                    'used': False,
                    'days': 30,
                    'price': PRO_PRICE,
                    'note': 'Тестовый код'
                }
            }
        
        if code in settings_db.get('pro_codes', {}):
            pro_data = settings_db['pro_codes'][code]
            
            if pro_data.get('used'):
                return jsonify({'success': False, 'message': 'Код уже использован'})
            
            if pro_data.get('expires') and datetime.fromisoformat(pro_data['expires']) < datetime.now():
                return jsonify({'success': False, 'message': 'Срок действия кода истёк'})
            
            user = users_db[user_id]
            days = pro_data.get('days', 30)
            
            user['is_pro'] = True
            user['pro_until'] = (datetime.now() + timedelta(days=days)).isoformat()
            user['pro_code'] = code
            user['limit'] = PRO_LIMIT
            
            pro_data['used'] = True
            pro_data['used_by'] = user_id
            pro_data['used_at'] = datetime.now().isoformat()
            
            return jsonify({
                'success': True,
                'message': f'🎉 PRO подписка активирована на {days} дней! Теперь у вас {PRO_LIMIT} запросов в день.'
            })
        
        return jsonify({'success': False, 'message': 'Неверный код активации'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

@app.route('/donation_info')
def donation_info():
    user_id = session.get('user_id', 'Неизвестен')
    
    content = f'''
    <div class="card">
        <h2><i class="fas fa-crown"></i> Получение PRO Подписки</h2>
        
        <div class="alert alert-success" style="margin-bottom: 25px;">
            <h3><i class="fas fa-gift"></i> Преимущества PRO:</h3>
            <ul style="margin: 10px 0 10px 20px;">
                <li><strong>{PRO_LIMIT} запросов в день</strong> (вместо {FREE_LIMIT})</li>
                <li>Приоритетная обработка запросов</li>
                <li>Расширенный контекст разговора</li>
                <li>Все экспертные роли</li>
                <li>Более детальные ответы</li>
            </ul>
        </div>
        
        <div class="alert" style="margin-bottom: 25px;">
            <h3><i class="fas fa-ruble-sign"></i> Стоимость</h3>
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 3rem; font-weight: bold; color: var(--gold);">
                    {PRO_PRICE} рублей
                </div>
                <div style="color: var(--muted);">за 30 дней использования</div>
            </div>
        </div>
        
        <div class="alert" style="margin-bottom: 25px;">
            <h3><i class="fas fa-qrcode"></i> Как получить PRO код?</h3>
            <div style="margin: 15px 0;">
                <p><strong>Способ 1:</strong> В админ-панели создайте PRO код</p>
                <p><strong>Способ 2:</strong> Сделайте донат {PRO_PRICE} рублей</p>
                <p><strong>Способ 3:</strong> Используйте тестовый код: <code>PRO-TEST123</code></p>
            </div>
            <p>Ваш ID для донатов: <code>{user_id}</code></p>
        </div>
        
        <div style="text-align: center;">
            <a href="/" class="btn btn-primary" style="padding: 15px 30px;">
                <i class="fas fa-arrow-left"></i> На главную
            </a>
            <a href="/admin" class="btn" style="padding: 15px 30px; margin-left: 10px;">
                <i class="fas fa-cog"></i> Админ-панель
            </a>
        </div>
    </div>
    '''
    
    return render_page(
        'PRO Подписка',
        '<div class="header"><h1 class="title"><i class="fas fa-crown"></i> PRO Подписка</h1></div>',
        '',
        content,
        '<div class="footer"><p>© 2024 Mateus AI</p></div>'
    )

# ==================== АДМИН ПАНЕЛЬ ====================

@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return '''
        <div style="max-width: 400px; margin: 100px auto; padding: 40px; background: #162416; border-radius: 20px; text-align: center;">
            <h2 style="color: #32cd32; margin-bottom: 30px;"><i class="fas fa-lock"></i> Админ-панель</h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Пароль администратора" 
                       style="width: 100%; padding: 15px; margin-bottom: 20px; border-radius: 10px; 
                              border: 1px solid #2a5c2a; background: rgba(0,0,0,0.3); color: white; font-size: 1rem;">
                <button type="submit" 
                        style="width: 100%; padding: 15px; background: #32cd32; border: none; 
                               border-radius: 10px; color: white; font-size: 1rem; font-weight: bold; cursor: pointer;">
                    <i class="fas fa-sign-in-alt"></i> Войти
                </button>
            </form>
            <p style="margin-top: 20px; color: #a3d9a3; font-size: 0.9rem;">
                По умолчанию: Admin123<br>
                Установите ADMIN_PASSWORD для безопасности
            </p>
        </div>
        '''
    
    users_total = len(users_db)
    pro_users = sum(1 for u in users_db.values() if u.get('is_pro'))
    requests_today = sum(u.get('requests_today', 0) for u in users_db.values())
    active_codes = sum(1 for c in settings_db.get('pro_codes', {}).values() if not c.get('used'))
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Админ-панель</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ background: #0a1a0a; color: #f0fff0; font-family: Arial, sans-serif; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; padding: 30px; background: #1a5d1a; border-radius: 15px; margin-bottom: 30px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .stat {{ background: #162416; padding: 20px; border-radius: 10px; text-align: center; }}
            .stat-value {{ font-size: 2.5rem; font-weight: bold; color: #32cd32; }}
            table {{ width: 100%; border-collapse: collapse; background: #162416; border-radius: 10px; overflow: hidden; margin: 20px 0; }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #2a5c2a; }}
            th {{ background: #2a5c2a; }}
            .btn {{ background: #32cd32; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
            .btn-danger {{ background: #ff6b6b; }}
            .btn-warning {{ background: #ffaa00; color: #333; }}
            form {{ margin: 20px 0; padding: 20px; background: #162416; border-radius: 10px; }}
            input, select {{ padding: 10px; margin: 5px; border-radius: 5px; border: 1px solid #2a5c2a; background: rgba(255,255,255,0.1); color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-cogs"></i> Админ-панель Mateus AI</h1>
                <p><a href="/" style="color: #90ee90;">← На главную</a> | Работает на Render.com</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div>👥 Пользователей</div>
                    <div class="stat-value">{users_total}</div>
                </div>
                <div class="stat">
                    <div>👑 PRO пользователей</div>
                    <div class="stat-value">{pro_users}</div>
                </div>
                <div class="stat">
                    <div>💬 Запросов сегодня</div>
                    <div class="stat-value">{requests_today}</div>
                </div>
                <div class="stat">
                    <div>🎫 Активных кодов</div>
                    <div class="stat-value">{active_codes}</div>
                </div>
            </div>
            
            <h2><i class="fas fa-ticket-alt"></i> Создать PRO код</h2>
            <form action="/admin/create_code" method="POST">
                <input type="hidden" name="password" value="{ADMIN_PASSWORD}">
                <div>
                    <label>Дней действия:</label>
                    <input type="number" name="days" value="30" min="1" max="365">
                </div>
                <div>
                    <label>Примечание:</label>
                    <input type="text" name="note" placeholder="Например: Тестовый код" style="width: 300px;">
                </div>
                <div>
                    <label>Тип кода:</label>
                    <select name="code_type">
                        <option value="pro">PRO подписка</option>
                        <option value="test">Тестовый</option>
                    </select>
                </div>
                <button type="submit" class="btn">
                    <i class="fas fa-plus"></i> Создать код
                </button>
            </form>
            
            <h2><i class="fas fa-users"></i> Пользователи ({len(users_db)})</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>PRO</th>
                    <th>Запросы</th>
                    <th>Создан</th>
                    <th>Действия</th>
                </tr>
                {''.join([f'''
                <tr>
                    <td><small>{uid[:12]}...</small></td>
                    <td>{"✅" if user.get('is_pro') else "❌"}</td>
                    <td>{user.get('requests_today', 0)}/{user.get('limit', FREE_LIMIT)}</td>
                    <td>{user.get('created', '')[:10] if user.get('created') else '-'}</td>
                    <td>
                        <button class="btn" onclick="togglePro('{uid}')">
                            {"❌ Снять PRO" if user.get('is_pro') else "✅ Дать PRO"}
                        </button>
                    </td>
                </tr>
                ''' for uid, user in list(users_db.items())[:30]])}
            </table>
            
            <h2><i class="fas fa-key"></i> PRO коды</h2>
            <table>
                <tr><th>Код</th><th>Срок</th><th>Статус</th><th>Примечание</th><th>Действия</th></tr>
                {''.join([f'''
                <tr>
                    <td><code>{code}</code></td>
                    <td>{data.get('expires', '')[0:10] if data.get('expires') else '∞'}</td>
                    <td>{"✅ Использован" if data.get('used') else "🟢 Активен"}</td>
                    <td>{data.get('note', '')}</td>
                    <td>
                        {'' if data.get('used') else f'<button class="btn-danger" onclick="deleteCode(\'{code}\')">Удалить</button>'}
                    </td>
                </tr>
                ''' for code, data in list(settings_db.get('pro_codes', {}).items())[:20]])}
            </table>
            
            <div style="margin-top: 40px; padding: 20px; background: #162416; border-radius: 10px;">
                <h3><i class="fas fa-info-circle"></i> Информация о системе</h3>
                <p><strong>OpenAI API:</strong> {'✅ Настроен' if client else '❌ Не настроен (используйте OPENAI_API_KEY)'}</p>
                <p><strong>Текущее время:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><strong>Статус:</strong> ✅ Работает на Render.com</p>
                <p><strong>Порт:</strong> {os.environ.get('PORT', '10000')}</p>
            </div>
        </div>
        
        <script>
            function togglePro(userId) {{
                if (confirm('Изменить PRO статус пользователя?')) {{
                    fetch(`/admin/toggle_pro/${{userId}}?password={ADMIN_PASSWORD}`, {{method: 'POST'}})
                        .then(() => location.reload());
                }}
            }}
            
            function deleteCode(code) {{
                if (confirm('Удалить этот код?')) {{
                    fetch(`/admin/delete_code/${{code}}?password={ADMIN_PASSWORD}`, {{method: 'DELETE'}})
                        .then(() => location.reload());
                }}
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/admin/toggle_pro/<user_id>', methods=['POST'])
def admin_toggle_pro(user_id):
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False})
    
    if user_id in users_db:
        users_db[user_id]['is_pro'] = not users_db[user_id].get('is_pro', False)
        users_db[user_id]['limit'] = PRO_LIMIT if users_db[user_id]['is_pro'] else FREE_LIMIT
        
        if users_db[user_id]['is_pro']:
            users_db[user_id]['pro_until'] = (datetime.now() + timedelta(days=30)).isoformat()
        else:
            users_db[user_id]['pro_until'] = None
    
    return jsonify({'success': True})

@app.route('/admin/create_code', methods=['POST'])
def create_pro_code():
    days = int(request.form.get('days', 30))
    note = request.form.get('note', '')
    password = request.form.get('password')
    code_type = request.form.get('code_type', 'pro')
    
    if password != ADMIN_PASSWORD:
        return redirect('/admin?password=' + ADMIN_PASSWORD)
    
    code = generate_pro_code()
    settings_db.setdefault('pro_codes', {})[code] = {
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=days)).isoformat(),
        'used': False,
        'note': note,
        'price': PRO_PRICE if code_type == 'pro' else 0,
        'type': code_type
    }
    
    return redirect(f'/admin?password={ADMIN_PASSWORD}')

@app.route('/admin/delete_code/<code>', methods=['DELETE'])
def delete_pro_code(code):
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False})
    
    if code in settings_db.get('pro_codes', {}):
        del settings_db['pro_codes'][code]
    
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Mateus AI',
        'timestamp': datetime.now().isoformat(),
        'users': len(users_db),
        'openai_configured': bool(client),
        'deploy_platform': 'Render.com',
        'version': '2.0'
    })

# ==================== ЗАПУСК СЕРВЕРА ====================

# Удаляем блок if __name__ == '__main__' для Render
# На Render приложение запускается через gunicorn
