"""
Mateus AI - Оптимизированная версия для Render.com
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

# Базовые настройки
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Для тестирования на Render, если ключ не установлен
    OPENAI_API_KEY = "sk-placeholder-for-testing" if os.environ.get('RENDER') else None
    print("⚠️  Warning: OPENAI_API_KEY not set, using placeholder")

try:
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception as e:
    print(f"⚠️  OpenAI client init error: {e}")
    client = None

# Лимиты
FREE_LIMIT = 10
PRO_LIMIT = 50  # Уменьшено для демонстрации на Render
PRO_PRICE = 1000

# Пароль админа
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123")

# Простое хранение данных в памяти (для демо на Render)
# В продакшене используйте базу данных
users_db = {}
settings_db = {
    'donation_alerts': {'connected': False},
    'pro_codes': {}
}

# ==================== HTML ШАБЛОН ====================

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
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a1a0a 0%, #0d3b0d 100%);
            color: #f0fff0;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            padding: 30px;
            background: rgba(26, 93, 26, 0.8);
            border-radius: 20px;
            margin-bottom: 30px;
            border: 2px solid #32cd32;
        }
        .logo {
            font-size: 3rem;
            color: #90ee90;
            margin-bottom: 15px;
        }
        .title {
            font-size: 2.5rem;
            color: #32cd32;
            margin-bottom: 10px;
        }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
        }
        @media (max-width: 768px) {
            .main-content { grid-template-columns: 1fr; }
        }
        .card {
            background: rgba(22, 36, 22, 0.8);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid #2a5c2a;
            margin-bottom: 20px;
        }
        .btn {
            background: linear-gradient(135deg, #1a5d1a, #2e8b57);
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
            margin: 5px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(46, 139, 87, 0.4);
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            border: 1px solid #2a5c2a;
            margin-bottom: 20px;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 12px;
            max-width: 80%;
        }
        .user-message {
            background: linear-gradient(135deg, #1a5d1a, #2e8b57);
            margin-left: auto;
            color: white;
        }
        .ai-message {
            background: rgba(46, 139, 87, 0.2);
            border: 1px solid #2a5c2a;
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
            border: 1px solid #2a5c2a;
            border-radius: 10px;
            color: #f0fff0;
            font-size: 1rem;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #a3d9a3;
            margin-top: 30px;
            border-top: 1px solid #2a5c2a;
        }
        .alert {
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .alert-error {
            background: rgba(255, 107, 107, 0.2);
            border: 1px solid #ff6b6b;
            color: #ff6b6b;
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
                
                addMessage('user', message);
                input.value = '';
                
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        addMessage('ai', data.response);
                    } else {
                        addMessage('ai', '<div class="alert alert-error">' + (data.error || 'Ошибка') + '</div>');
                    }
                })
                .catch(() => {
                    addMessage('ai', '<div class="alert alert-error">Ошибка соединения</div>');
                });
            };
            
            // Enter для отправки
            document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        });
        
        function addMessage(sender, text) {
            const chat = document.getElementById('chatMessages');
            if (!chat) return;
            
            const div = document.createElement('div');
            div.className = `message ${sender}-message`;
            div.innerHTML = `<strong>${sender === 'user' ? '👤 Вы' : '🤖 AI'}:</strong><br>${text}`;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function selectRole(role) {
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role: role})
            }).then(() => alert('Роль изменена: ' + role));
        }
    </script>
</body>
</html>
'''

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_user_id():
    user_id = session.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        session['user_id'] = user_id
    
    if user_id not in users_db:
        users_db[user_id] = {
            'id': user_id,
            'requests_today': 0,
            'last_request': datetime.now().date().isoformat(),
            'is_pro': False,
            'limit': FREE_LIMIT
        }
    
    return user_id

def check_request_limit(user_id):
    user = users_db.get(user_id, {})
    today = datetime.now().date().isoformat()
    
    if user.get('last_request') != today:
        user['requests_today'] = 0
        user['last_request'] = today
    
    limit = PRO_LIMIT if user.get('is_pro') else FREE_LIMIT
    used = user.get('requests_today', 0)
    return used < limit, limit, used

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    user_id = get_user_id()
    can_request, limit, used = check_request_limit(user_id)
    remaining = limit - used
    
    header = f'''
    <div class="header">
        <div class="logo"><i class="fas fa-brain"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p>Запросов: {used}/{limit} | Осталось: {remaining}</p>
        <p><small>Версия для Render.com</small></p>
    </div>
    '''
    
    sidebar = f'''
    <div class="card">
        <h3>Роли AI:</h3>
        <button class="btn" onclick="selectRole('assistant')"><i class="fas fa-robot"></i> Помощник</button>
        <button class="btn" onclick="selectRole('teacher')"><i class="fas fa-graduation-cap"></i> Учитель</button>
        <button class="btn" onclick="selectRole('programmer')"><i class="fas fa-code"></i> Программист</button>
    </div>
    '''
    
    content = f'''
    <div class="card">
        <h3>Чат с Mateus AI</h3>
        <div id="chatMessages" class="chat-messages">
            <div class="ai-message">
                <strong>🤖 Mateus AI:</strong><br>
                Привет! Я ваш AI помощник. Вы можете задавать вопросы на любые темы.
                {'' if client else '<br><br><div class="alert alert-error">⚠️ OpenAI API не настроен. Некоторые функции могут быть недоступны.</div>'}
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Введите ваш вопрос..." autofocus>
            <button class="btn" onclick="sendMessage()">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
    </div>
    '''
    
    footer = f'''
    <div class="footer">
        <p>Mateus AI © 2024 | Render.com Deploy</p>
        <p><a href="/health" style="color: #32cd32;">Проверка работоспособности</a></p>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE, 
        header=header, 
        sidebar=sidebar, 
        content=content, 
        footer=footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    data = request.get_json()
    role = data.get('role', 'assistant')
    session['current_role'] = role
    return jsonify({'success': True, 'role': role})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = get_user_id()
        
        can_request, limit, used = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': f'Достигнут лимит запросов ({used}/{limit}). Обновите страницу для сброса.'
            })
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'AI сервис временно недоступен. Проверьте настройки API.'
            })
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})
        
        # Простое эхо-ответ для тестирования, если OpenAI не работает
        if OPENAI_API_KEY == "sk-placeholder-for-testing":
            users_db[user_id]['requests_today'] = users_db.get(user_id, {}).get('requests_today', 0) + 1
            return jsonify({
                'success': True,
                'response': f'Вы сказали: "{message}".\n\nПримечание: OpenAI API не настроен. Для работы с AI установите OPENAI_API_KEY.'
            })
        
        try:
            # Запрос к OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - полезный помощник Mateus AI. Отвечай кратко и по делу."},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            answer = response.choices[0].message.content
            users_db[user_id]['requests_today'] = users_db.get(user_id, {}).get('requests_today', 0) + 1
            
            return jsonify({'success': True, 'response': answer})
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Ошибка AI сервиса: {str(e)}'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка сервера: {str(e)}'})

@app.route('/health')
def health_check():
    """Проверка работоспособности для Render"""
    return jsonify({
        'status': 'ok',
        'service': 'Mateus AI',
        'timestamp': datetime.now().isoformat(),
        'users_count': len(users_db),
        'openai_configured': bool(client and OPENAI_API_KEY != "sk-placeholder-for-testing")
    })

@app.route('/admin')
def admin():
    """Простая админка для проверки"""
    password = request.args.get('pwd')
    if password != ADMIN_PASSWORD:
        return '''
        <div style="max-width: 400px; margin: 100px auto; padding: 30px; background: #162416; border-radius: 15px;">
            <h2 style="color: #32cd32; margin-bottom: 20px;">Админ-панель Mateus AI</h2>
            <form>
                <input type="password" name="pwd" placeholder="Пароль администратора" 
                       style="width: 100%; padding: 12px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.3); color: white;">
                <button type="submit" 
                        style="width: 100%; padding: 12px; background: #32cd32; border: none; border-radius: 8px; color: white; font-weight: bold;">
                    Войти
                </button>
            </form>
        </div>
        '''
    
    stats = {
        'users': len(users_db),
        'pro_users': sum(1 for u in users_db.values() if u.get('is_pro')),
        'requests_today': sum(u.get('requests_today', 0) for u in users_db.values()),
        'openai_status': '✅ Настроен' if client and OPENAI_API_KEY != "sk-placeholder-for-testing" else '⚠️ Тестовый режим'
    }
    
    return f'''
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #32cd32;">Админ-панель Mateus AI</h1>
        <a href="/" style="color: #90ee90; text-decoration: none;">← На главную</a>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="background: #1a5d1a; padding: 20px; border-radius: 10px;">
                <h3>👥 Пользователей</h3>
                <p style="font-size: 2rem; font-weight: bold;">{stats['users']}</p>
            </div>
            <div style="background: #9775fa; padding: 20px; border-radius: 10px;">
                <h3>👑 PRO пользователей</h3>
                <p style="font-size: 2rem; font-weight: bold;">{stats['pro_users']}</p>
            </div>
            <div style="background: #2e8b57; padding: 20px; border-radius: 10px;">
                <h3>💬 Запросов сегодня</h3>
                <p style="font-size: 2rem; font-weight: bold;">{stats['requests_today']}</p>
            </div>
            <div style="background: #4dabf7; padding: 20px; border-radius: 10px;">
                <h3>🤖 OpenAI</h3>
                <p style="font-size: 1.2rem; font-weight: bold;">{stats['openai_status']}</p>
            </div>
        </div>
        
        <h2>Последние пользователи</h2>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: rgba(0,0,0,0.2); border-radius: 10px; overflow: hidden;">
                <tr style="background: #2a5c2a;">
                    <th style="padding: 15px; text-align: left;">ID</th>
                    <th style="padding: 15px; text-align: left;">Статус</th>
                    <th style="padding: 15px; text-align: left;">Запросы</th>
                </tr>
                {"".join([f'''
                <tr style="border-bottom: 1px solid #2a5c2a;">
                    <td style="padding: 12px;">{uid[:12]}...</td>
                    <td style="padding: 12px;">{"👑 PRO" if user.get('is_pro') else "👤 Free"}</td>
                    <td style="padding: 12px;">{user.get('requests_today', 0)}</td>
                </tr>
                ''' for uid, user in list(users_db.items())[:20]])}
            </table>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 10px;">
            <h3>Информация о системе</h3>
            <p>Сервис запущен на Render.com</p>
            <p>Текущее время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Для настройки OpenAI API установите переменную окружения OPENAI_API_KEY</p>
        </div>
    </div>
    '''

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    # Render автоматически устанавливает PORT
    port = int(os.environ.get('PORT', 10000))
    
    print("=" * 60)
    print("🤖 Mateus AI - Запуск на Render.com")
    print("=" * 60)
    print(f"🌐 Порт: {port}")
    print(f"🔑 OpenAI: {'✅ Настроен' if client and OPENAI_API_KEY != 'sk-placeholder-for-testing' else '⚠️ Тестовый режим'}")
    print(f"🔐 Админ пароль: {'✅ Настроен' if ADMIN_PASSWORD != 'Admin123' else '⚠️ Используйте переменную ADMIN_PASSWORD'}")
    print("=" * 60)
    print(f"🚀 Сервер запущен: http://0.0.0.0:{port}")
    print("=" * 60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False
        )
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("Попробуйте другой порт...")
        app.run(host='0.0.0.0', port=5000, debug=False)
