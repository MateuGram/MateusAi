"""
Mateus AI - Рабочая версия для Render.com
"""

import os
import uuid
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== КОНФИГУРАЦИЯ ====================

# Лимиты
FREE_LIMIT = 10
PRO_LIMIT = 1000
PRO_PRICE = 1000

# Пароль админа
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin123")

# ==================== ХРАНЕНИЕ ДАННЫХ ====================

users_db = {}
settings_db = {'pro_codes': {}}

# ==================== HTML ШАБЛОНЫ ====================

BASE_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #1a5d1a; --secondary: #2e8b57; --light: #90ee90;
            --accent: #32cd32; --dark: #0d3b0d; --background: #0a1a0a;
            --card: #162416; --text: #f0fff0; --muted: #a3d9a3;
            --border: #2a5c2a; --gold: #ffd700; --blue: #4dabf7;
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
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center; padding: 40px 30px;
            background: linear-gradient(135deg, var(--primary), var(--dark));
            border-radius: 20px; margin-bottom: 40px;
            border: 2px solid var(--accent);
        }
        .logo { font-size: 3.5rem; color: var(--light); margin-bottom: 10px; }
        .title { 
            font-size: 3rem; 
            background: linear-gradient(45deg, var(--light), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px; 
        }
        .main-content { display: grid; grid-template-columns: 1fr 3fr; gap: 30px; }
        @media (max-width: 1100px) { .main-content { grid-template-columns: 1fr; } }
        .card {
            background: var(--card); border-radius: 15px;
            padding: 30px; border: 1px solid var(--border);
            margin-bottom: 20px;
        }
        .btn {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none; color: white; padding: 12px 24px;
            border-radius: 10px; cursor: pointer; font-size: 1rem;
            transition: all 0.3s; display: inline-flex;
            align-items: center; gap: 10px;
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(46,139,87,0.4); }
        .chat-messages {
            height: 500px; overflow-y: auto; margin-bottom: 25px;
            padding: 20px; background: rgba(0,0,0,0.2);
            border-radius: 10px; border: 1px solid var(--border);
        }
        .message {
            margin-bottom: 20px; padding: 15px; border-radius: 12px;
            max-width: 85%;
        }
        .user-message { background: linear-gradient(135deg, var(--primary), var(--secondary)); margin-left: auto; color: white; }
        .ai-message { background: rgba(46,139,87,0.2); border: 1px solid var(--border); margin-right: auto; }
        .chat-input { display: flex; gap: 15px; }
        .chat-input input {
            flex: 1; padding: 15px; background: rgba(0,0,0,0.3);
            border: 1px solid var(--border); border-radius: 10px;
            color: var(--text); font-size: 1rem;
        }
        .footer { 
            text-align: center; padding: 30px; color: var(--muted);
            border-top: 1px solid var(--border); margin-top: 40px; 
        }
    </style>
</head>
<body>
    <div class="container">
        {{ header|safe }}
        <div class="main-content">
            {{ sidebar|safe }}
            {{ content|safe }}
        </div>
        {{ footer|safe }}
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            window.sendMessage = function() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                const btn = document.querySelector('.chat-input .btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                btn.disabled = true;
                
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
                        addMessage('ai', '<div style="color: var(--red);">' + data.error + '</div>');
                    }
                })
                .catch(error => {
                    addMessage('ai', '<div style="color: var(--red);">Ошибка сети</div>');
                })
                .finally(() => {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    input.focus();
                });
            };
            
            document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
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
            div.className = 'message ' + sender + '-message';
            div.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 8px;">
                    ${sender === 'user' ? '👤 Вы' : '🤖 Mateus AI'}
                </div>
                <div>${text}</div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>'''

def render_page(title, header, sidebar, content, footer):
    return render_template_string(BASE_HTML, 
        title=title, 
        header=header, 
        sidebar=sidebar, 
        content=content, 
        footer=footer
    )

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
    remaining = limit - used
    
    return used < limit, limit, used, remaining

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used, remaining = check_request_limit(user_id)
    
    header = '''
    <div class="header">
        <a href="/admin" style="position: absolute; top: 20px; right: 20px; color: #32cd32;">
            <i class="fas fa-cog"></i> Админ
        </a>
        <div class="logo"><i class="fas fa-brain"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p>Интеллектуальный помощник нового поколения</p>
        
        <div style="margin-top: 20px;">
            <span style="background: rgba(50,205,50,0.15); color: #32cd32; padding: 8px 16px; border-radius: 20px;">
                <i class="fas fa-''' + ('rocket' if can_request else 'hourglass-end') + '''"></i>
                ''' + str(used) + '''/''' + str(limit) + ''' запросов | Осталось: ''' + str(remaining) + '''
            </span>
            ''' + ('<span style="background: gold; color: #333; padding: 4px 12px; border-radius: 20px; margin-left: 10px;">PRO</span>' if user.get('is_pro') else '') + '''
        </div>
    </div>
    '''
    
    sidebar = '''
    <div class="card">
        <h3><i class="fas fa-mask"></i> Роли AI</h3>
        <div style="margin: 20px 0;">
            <button class="btn" onclick="selectRole('assistant')" style="width: 100%; margin-bottom: 10px;">
                <i class="fas fa-robot"></i> Помощник
            </button>
            <button class="btn" onclick="selectRole('programmer')" style="width: 100%; margin-bottom: 10px;">
                <i class="fas fa-code"></i> Программист
            </button>
            <button class="btn" onclick="selectRole('teacher')" style="width: 100%; margin-bottom: 10px;">
                <i class="fas fa-graduation-cap"></i> Учитель
            </button>
        </div>
        
        <div style="background: rgba(151,117,250,0.1); padding: 20px; border-radius: 15px; border: 1px solid #9775fa;">
            <h4><i class="fas fa-crown"></i> PRO Подписка</h4>
            <p>''' + str(PRO_PRICE) + ''' руб. / ''' + str(PRO_LIMIT) + ''' запросов в день</p>
            <input type="text" id="proCode" placeholder="Введите PRO код" 
                   style="width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.2); color: white;">
            <button class="btn" onclick="activatePro()" style="width: 100%; background: gold; color: #333;">
                <i class="fas fa-bolt"></i> Активировать PRO
            </button>
            <p style="text-align: center; margin-top: 10px;">
                <a href="/donation_info" style="color: #9775fa; text-decoration: none;">
                    <i class="fas fa-donate"></i> Как получить код?
                </a>
            </p>
        </div>
    </div>
    
    <script>
        function selectRole(role) {
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role: role})
            }).then(() => alert('Роль "' + role + '" выбрана'));
        }
    </script>
    '''
    
    content = '''
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
                    </ul>
                    <p>Выберите роль слева и задавайте вопросы!</p>
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Введите ваш вопрос... (Enter для отправки)" autofocus>
            <button class="btn" onclick="sendMessage()" style="background: #32cd32; color: #0d3b0d;">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
    </div>
    '''
    
    footer = '''
    <div class="footer">
        <p>© 2024 Mateus AI | Искусственный интеллект нового поколения</p>
        <p>Работает на Render.com | Free: ''' + str(FREE_LIMIT) + '''/день | PRO: ''' + str(PRO_LIMIT) + '''/день</p>
    </div>
    '''
    
    return render_page('Mateus AI', header, sidebar, content, footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    session['role'] = request.get_json().get('role', 'assistant')
    return jsonify({'success': True})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = get_user_id()
        
        can_request, limit, used, remaining = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': 'Лимит запросов исчерпан (' + str(used) + '/' + str(limit) + '). Купите PRO подписку!'
            })
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})
        
        # Простой ответ для демонстрации
        import random
        responses = [
            "Вы спросили: '" + message + "'. Это интересный вопрос! Mateus AI готов помочь вам.",
            "Вопрос принят: '" + message[:50] + "...'. Я обрабатываю ваш запрос.",
            "Спасибо за сообщение! Вы использовали " + str(used + 1) + " из " + str(limit) + " запросов на сегодня.",
            "Отличный вопрос! Mateus AI анализирует информацию чтобы дать вам лучший ответ."
        ]
        
        response = random.choice(responses)
        
        users_db[user_id]['requests_today'] = used + 1
        
        return jsonify({
            'success': True,
            'response': response,
            'usage': {
                'used': used + 1,
                'limit': limit,
                'remaining': remaining - 1
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/activate_pro', methods=['POST'])
def activate_pro():
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return jsonify({'success': False, 'message': 'Введите код'})
        
        user_id = get_user_id()
        
        # Тестовый код
        if code == "PRO-TEST123":
            users_db[user_id]['is_pro'] = True
            users_db[user_id]['limit'] = PRO_LIMIT
            return jsonify({
                'success': True,
                'message': 'PRO подписка активирована на 30 дней!'
            })
        
        # Проверка кодов из settings
        if code in settings_db.get('pro_codes', {}):
            pro_data = settings_db['pro_codes'][code]
            
            if not pro_data.get('used'):
                users_db[user_id]['is_pro'] = True
                users_db[user_id]['limit'] = PRO_LIMIT
                pro_data['used'] = True
                
                return jsonify({
                    'success': True,
                    'message': 'PRO подписка активирована!'
                })
        
        return jsonify({'success': False, 'message': 'Неверный код'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/donation_info')
def donation_info():
    return '''
    <div style="max-width: 800px; margin: 0 auto; padding: 40px;">
        <div style="background: #162416; padding: 40px; border-radius: 20px; border: 2px solid #32cd32;">
            <h1 style="color: #32cd32; text-align: center;">PRO Подписка Mateus AI</h1>
            <div style="text-align: center; margin: 30px 0;">
                <div style="font-size: 3rem; color: gold; font-weight: bold;">''' + str(PRO_PRICE) + ''' ₽</div>
                <div style="color: #a3d9a3;">за 30 дней использования</div>
            </div>
            <div style="background: rgba(50,205,50,0.1); padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #32cd32;">Преимущества PRO:</h3>
                <ul style="color: #f0fff0;">
                    <li>''' + str(PRO_LIMIT) + ''' запросов в день (вместо ''' + str(FREE_LIMIT) + ''')</li>
                    <li>Приоритетная обработка запросов</li>
                    <li>Расширенный контекст разговора</li>
                    <li>Все экспертные роли</li>
                </ul>
            </div>
            <div style="text-align: center; margin-top: 40px;">
                <a href="/" style="background: #32cd32; color: #0d3b0d; padding: 15px 30px; border-radius: 10px; text-decoration: none; font-weight: bold;">
                    <i class="fas fa-arrow-left"></i> На главную
                </a>
            </div>
        </div>
    </div>
    '''

@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return '''
        <div style="max-width: 400px; margin: 100px auto; padding: 40px; background: #162416; border-radius: 20px; text-align: center;">
            <h2 style="color: #32cd32;">Админ-панель</h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Пароль" 
                       style="width: 100%; padding: 12px; margin: 20px 0; border-radius: 8px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.3); color: white;">
                <button type="submit" 
                        style="width: 100%; padding: 12px; background: #32cd32; border: none; border-radius: 8px; color: white;">
                    Войти
                </button>
            </form>
        </div>
        '''
    
    users_total = len(users_db)
    pro_users = sum(1 for u in users_db.values() if u.get('is_pro'))
    requests_today = sum(u.get('requests_today', 0) for u in users_db.values())
    
    html = '''
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #32cd32;">Админ-панель Mateus AI</h1>
        <p><a href="/" style="color: #90ee90;">← На главную</a></p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="background: #1a5d1a; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>👥 Пользователей</h3>
                <p style="font-size: 2.5rem;">''' + str(users_total) + '''</p>
            </div>
            <div style="background: #9775fa; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>👑 PRO</h3>
                <p style="font-size: 2.5rem;">''' + str(pro_users) + '''</p>
            </div>
            <div style="background: #2e8b57; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>💬 Запросы сегодня</h3>
                <p style="font-size: 2.5rem;">''' + str(requests_today) + '''</p>
            </div>
        </div>
        
        <h2>Создать PRO код</h2>
        <form method="POST" action="/admin/create_code">
            <input type="hidden" name="password" value="''' + ADMIN_PASSWORD + '''">
            <input type="number" name="days" value="30" style="padding: 10px; margin: 5px;">
            <input type="text" name="note" placeholder="Примечание" style="padding: 10px; margin: 5px;">
            <button type="submit" style="padding: 10px 20px; background: #32cd32; border: none; border-radius: 5px; color: white;">
                Создать код
            </button>
        </form>
        
        <h2>Пользователи</h2>
        <table style="width: 100%; border-collapse: collapse; background: #162416; border-radius: 10px; overflow: hidden; margin: 20px 0;">
            <tr style="background: #2a5c2a;">
                <th style="padding: 15px;">ID</th>
                <th style="padding: 15px;">PRO</th>
                <th style="padding: 15px;">Запросы</th>
            </tr>
    '''
    
    for uid, user in list(users_db.items())[:20]:
        html += '''
            <tr style="border-bottom: 1px solid #2a5c2a;">
                <td style="padding: 12px;">''' + uid[:12] + '''...</td>
                <td style="padding: 12px;">''' + ('✅' if user.get('is_pro') else '❌') + '''</td>
                <td style="padding: 12px;">''' + str(user.get('requests_today', 0)) + '''</td>
            </tr>
        '''
    
    html += '''
        </table>
    </div>
    '''
    
    return html

@app.route('/admin/create_code', methods=['POST'])
def create_pro_code():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return "Ошибка доступа"
    
    code = "PRO-" + secrets.token_hex(4).upper()
    days = int(request.form.get('days', 30))
    note = request.form.get('note', '')
    
    settings_db.setdefault('pro_codes', {})[code] = {
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=days)).isoformat(),
        'used': False,
        'note': note
    }
    
    return '<script>alert("Код создан: ' + code + '"); location.href="/admin?password=' + ADMIN_PASSWORD + '";</script>'

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Mateus AI',
        'timestamp': datetime.now().isoformat(),
        'users': len(users_db),
        'version': '2.0'
    })

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    # Для локального тестирования
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Запуск Mateus AI на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
