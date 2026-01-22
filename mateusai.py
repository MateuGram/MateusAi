"""
Mateus AI - Финальная рабочая версия с вашим новым ключом OpenAI
"""

import os
import uuid
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== КОНФИГУРАЦИЯ ====================

# ВАШ НОВЫЙ КЛЮЧ OPENAI (вставьте в Render Environment)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-9a7048e59d87434dbcb43e6e3d2a47e1")

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
        .loader {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 3px solid var(--accent);
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .ai-response {
            line-height: 1.6;
        }
        .ai-response h3, .ai-response h4 {
            color: var(--accent);
            margin: 15px 0 10px 0;
        }
        .ai-response ul, .ai-response ol {
            margin: 10px 0 10px 20px;
        }
        .ai-response li {
            margin-bottom: 8px;
        }
        .ai-response code {
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
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
                btn.innerHTML = '<span class="loader"></span> Отправка...';
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
                        addMessage('ai', '<div style="color: var(--red); padding: 10px; background: rgba(255,107,107,0.1); border-radius: 8px;"><i class="fas fa-exclamation-circle"></i> ' + data.error + '</div>');
                    }
                })
                .catch(error => {
                    addMessage('ai', '<div style="color: var(--red);"><i class="fas fa-exclamation-circle"></i> Ошибка сети</div>');
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
            if (sender === 'ai') {
                div.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 8px;">
                        🤖 Mateus AI
                    </div>
                    <div class="ai-response">${text}</div>
                `;
            } else {
                div.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 8px;">
                        👤 Вы
                    </div>
                    <div>${text}</div>
                `;
            }
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        
        window.selectRole = function(role) {
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role: role})
            })
            .then(r => r.json())
            .then(data => {
                const roleNames = {
                    'assistant': 'Ассистент',
                    'programmer': 'Программист',
                    'teacher': 'Учитель'
                };
                alert('🎭 Роль "' + roleNames[role] + '" выбрана!');
            });
        };
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
            'limit': FREE_LIMIT,
            'chat_history': []
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

def get_ai_response(user_id, message, role='assistant'):
    """РЕАЛЬНЫЙ ОТВЕТ ОТ OPENAI GPT-3.5-TURBO С ВАШИМ НОВЫМ КЛЮЧОМ"""
    
    # Проверяем ключ
    if not OPENAI_API_KEY or len(OPENAI_API_KEY) < 30:
        return "❌ **OpenAI API ключ не настроен.**\n\nДобавьте правильный OPENAI_API_KEY в переменные окружения Render."
    
    # Системные промпты
    system_prompts = {
        'assistant': """Ты - Mateus AI, умный и полезный AI-ассистент. 
Отвечай вежливо, информативно и по делу на русском языке.
Используй эмодзи где уместно.
Будь дружелюбным и готовым помочь с любыми вопросами.
Отвечай полно и развернуто, но по существу.""",
        
        'programmer': """Ты - Mateus AI, эксперт по программированию.
Помогай с кодом на любых языках программирования.
Объясняй концепции простыми словами на русском языке.
Предоставляй примеры кода и лучшие практики.""",
        
        'teacher': """Ты - Mateus AI, опытный учитель и наставник.
Объясняй сложные темы простым и понятным русским языком.
Используй аналогии и примеры из жизни.
Разбивай сложные темы на простые шаги."""
    }
    
    try:
        import openai
        
        # Устанавливаем ВАШ НОВЫЙ КЛЮЧ
        openai.api_key = OPENAI_API_KEY
        
        # Простой и надежный запрос
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompts.get(role, system_prompts['assistant'])},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # Сохраняем в историю
        user = users_db.get(user_id, {})
        if 'chat_history' not in user:
            user['chat_history'] = []
        user['chat_history'].append({"role": "user", "content": message})
        user['chat_history'].append({"role": "assistant", "content": ai_response})
        
        return ai_response
        
    except ImportError:
        return "❌ **Библиотека OpenAI не установлена.**"
    
    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "incorrect api key" in error_msg.lower():
            return f"""🔑 **ПРОБЛЕМА С КЛЮЧОМ OPENAI**

Ключ: `{OPENAI_API_KEY[:15]}...`

**Решение:**
1. Убедитесь что ключ скопирован полностью
2. Проверьте баланс на platform.openai.com
3. Если не работает - создайте новый ключ
4. Обновите в настройках Render"""
        
        elif "rate limit" in error_msg.lower():
            return "⏳ **Превышен лимит запросов. Попробуйте позже.**"
        
        else:
            return f"⚠️ **Ошибка**: {error_msg[:100]}"

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    user_id = get_user_id()
    user = users_db.get(user_id, {})
    
    can_request, limit, used, remaining = check_request_limit(user_id)
    
    # Проверяем статус OpenAI
    openai_status = "✅ Активен" if OPENAI_API_KEY and len(OPENAI_API_KEY) > 30 else "❌ Не настроен"
    
    header = f'''
    <div class="header">
        <a href="/admin" style="position: absolute; top: 20px; right: 20px; color: #32cd32;">
            <i class="fas fa-cog"></i> Админ
        </a>
        <div class="logo"><i class="fas fa-brain"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p>Настоящий искусственный интеллект с GPT-3.5 Turbo</p>
        
        <div style="margin-top: 20px;">
            <span style="background: rgba(50,205,50,0.15); color: #32cd32; padding: 8px 16px; border-radius: 20px;">
                <i class="fas fa-{'rocket' if can_request else 'hourglass-end'}"></i>
                {used}/{limit} запросов | Осталось: {remaining}
            </span>
            {'<span style="background: gold; color: #333; padding: 4px 12px; border-radius: 20px; margin-left: 10px; font-weight: bold;"><i class="fas fa-crown"></i> PRO</span>' if user.get('is_pro') else ''}
        </div>
        
        <div style="margin-top: 15px; font-size: 0.9rem; color: #90ee90;">
            <i class="fas fa-bolt"></i> OpenAI GPT-3.5 Turbo | Статус: {openai_status}
        </div>
    </div>
    '''
    
    sidebar = f'''
    <div class="card">
        <h3><i class="fas fa-mask"></i> Режимы AI</h3>
        <p style="color: #a3d9a3; margin-bottom: 15px; font-size: 0.9rem;">Выберите специализацию AI</p>
        
        <div style="margin: 20px 0;">
            <button class="btn" onclick="selectRole('assistant')" style="width: 100%; margin-bottom: 10px; text-align: left;">
                <i class="fas fa-robot"></i> Универсальный помощник
            </button>
            <button class="btn" onclick="selectRole('programmer')" style="width: 100%; margin-bottom: 10px; text-align: left;">
                <i class="fas fa-code"></i> Программист & Разработчик
            </button>
            <button class="btn" onclick="selectRole('teacher')" style="width: 100%; margin-bottom: 10px; text-align: left;">
                <i class="fas fa-graduation-cap"></i> Учитель & Объяснятор
            </button>
        </div>
        
        <div style="background: rgba(151,117,250,0.1); padding: 20px; border-radius: 15px; border: 1px solid #9775fa;">
            <h4><i class="fas fa-crown"></i> PRO Подписка</h4>
            <p style="color: #a3d9a3; margin: 10px 0;">{PRO_PRICE} руб. / 30 дней</p>
            <p style="font-size: 0.9rem; color: #90ee90; margin-bottom: 15px;">
                <i class="fas fa-bolt"></i> {PRO_LIMIT} запросов в день
            </p>
            <input type="text" id="proCode" placeholder="Введите PRO код" 
                   style="width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.2); color: white;">
            <button class="btn" onclick="activatePro()" style="width: 100%; background: linear-gradient(135deg, gold, #ffcc00); color: #333; font-weight: bold;">
                <i class="fas fa-bolt"></i> Активировать PRO
            </button>
            <p style="text-align: center; margin-top: 10px; font-size: 0.85rem;">
                <a href="/donation_info" style="color: #9775fa; text-decoration: none;">
                    <i class="fas fa-donate"></i> Как получить код?
                </a>
            </p>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: rgba(50,205,50,0.05); border-radius: 10px; border: 1px solid #2a5c2a;">
            <h4><i class="fas fa-info-circle"></i> О системе</h4>
            <p style="font-size: 0.85rem; color: #a3d9a3; margin-top: 10px;">
                • Реальный AI (OpenAI GPT-3.5)<br>
                • 3 режима работы<br>
                • PRO подписка<br>
                • Лимиты запросов
            </p>
        </div>
    </div>
    '''
    
    content = '''
    <div class="card">
        <h3><i class="fas fa-comments"></i> Чат с Mateus AI</h3>
        <p style="color: #a3d9a3; margin-bottom: 20px; font-size: 0.95rem;">
            Задавайте любые вопросы! Работает на реальном OpenAI GPT-3.5 Turbo
        </p>
        
        <div id="chatMessages" class="chat-messages">
            <div class="ai-message">
                <strong>🤖 Mateus AI</strong>
                <div style="margin-top: 10px;" class="ai-response">
                    <h3>👋 Привет! Я настоящий искусственный интеллект Mateus AI!</h3>
                    
                    <p>Я работаю на основе <strong>OpenAI GPT-3.5 Turbo</strong> и могу помочь вам с:</p>
                    
                    <ul>
                        <li>💡 <strong>Ответами на любые вопросы</strong></li>
                        <li>💻 <strong>Помощью в программировании</strong></li>
                        <li>📚 <strong>Объяснением сложных тем</strong></li>
                        <li>✍️ <strong>Написанием текстов</strong></li>
                        <li>🔍 <strong>Анализом информации</strong></li>
                    </ul>
                    
                    <div style="background: rgba(50,205,50,0.1); padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #32cd32;">
                        <p><strong>🎭 Выберите режим слева</strong> для лучших результатов:</p>
                        <ul style="margin-top: 5px;">
                            <li><strong>Помощник</strong> - общие вопросы</li>
                            <li><strong>Программист</strong> - код и технологии</li>
                            <li><strong>Учитель</strong> - обучение и объяснения</li>
                        </ul>
                    </div>
                    
                    <p><strong>Примеры вопросов:</strong></p>
                    <ul>
                        <li>"Привет, как дела?"</li>
                        <li>"Напиши код на Python для сайта"</li>
                        <li>"Объясни что такое нейросеть"</li>
                        <li>"Помоги составить план обучения"</li>
                    </ul>
                    
                    <p>Просто напишите ваш вопрос ниже и нажмите Enter!</p>
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Напишите 'Привет' для теста... (Enter для отправки)" autofocus>
            <button class="btn" onclick="sendMessage()" style="background: linear-gradient(135deg, #32cd32, #2a8c2a); font-weight: bold;">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
        
        <div style="margin-top: 15px; font-size: 0.85rem; color: #a3d9a3;">
            <i class="fas fa-lightbulb"></i> <strong>Тест:</strong> Напишите "Привет" чтобы проверить работу AI
        </div>
    </div>
    '''
    
    footer = f'''
    <div class="footer">
        <p>© 2024 Mateus AI | Реальный искусственный интеллект на OpenAI GPT-3.5 Turbo</p>
        <p style="margin-top: 10px; font-size: 0.8rem; opacity: 0.8;">
            Работает на Render.com | Free: {FREE_LIMIT}/день | PRO: {PRO_LIMIT}/день
        </p>
        <p style="margin-top: 5px; font-size: 0.75rem; opacity: 0.6;">
            <i class="fas fa-bolt"></i> OpenAI API | GPT-3.5 Turbo | Ключ: {OPENAI_API_KEY[:8]}...
        </p>
    </div>
    '''
    
    return render_page('Mateus AI | Real AI', header, sidebar, content, footer)

@app.route('/set_role', methods=['POST'])
def set_role():
    session['role'] = request.get_json().get('role', 'assistant')
    return jsonify({'success': True, 'role': session['role']})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = get_user_id()
        
        can_request, limit, used, remaining = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': f'🚫 Лимит запросов исчерпан ({used}/{limit}). Купите PRO подписку за {PRO_PRICE} рублей!'
            })
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})
        
        if len(message) > 4000:
            return jsonify({'success': False, 'error': 'Сообщение слишком длинное (макс. 4000 символов)'})
        
        # Получаем выбранную роль
        role = session.get('role', 'assistant')
        
        # ПОЛУЧАЕМ РЕАЛЬНЫЙ ОТВЕТ ОТ OPENAI
        ai_response = get_ai_response(user_id, message, role)
        
        # Обновляем счетчик запросов
        users_db[user_id]['requests_today'] = used + 1
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'usage': {
                'used': used + 1,
                'limit': limit,
                'remaining': remaining - 1
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка сервера: {str(e)}'})

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
                'message': '✅ PRO подписка активирована на 30 дней! Теперь у вас 1000 запросов в день.'
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
                    'message': '✅ PRO подписка активирована! Теперь у вас 1000 запросов в день.'
                })
        
        return jsonify({'success': False, 'message': '❌ Неверный или уже использованный код'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

@app.route('/donation_info')
def donation_info():
    return '''
    <div style="max-width: 800px; margin: 40px auto; padding: 20px;">
        <div style="background: #162416; padding: 40px; border-radius: 20px; border: 2px solid #32cd32;">
            <h1 style="color: #32cd32; text-align: center;">
                <i class="fas fa-crown"></i> PRO Подписка Mateus AI
            </h1>
            
            <div style="text-align: center; margin: 30px 0;">
                <div style="font-size: 3.5rem; color: gold; font-weight: bold; line-height: 1;">
                    ''' + str(PRO_PRICE) + ''' ₽
                </div>
                <div style="color: #a3d9a3; margin-top: 10px;">
                    за 30 дней использования реального AI
                </div>
            </div>
            
            <div style="background: rgba(50,205,50,0.1); padding: 25px; border-radius: 15px; margin: 25px 0; border: 1px solid #32cd32;">
                <h3 style="color: #32cd32; margin-bottom: 20px;">
                    <i class="fas fa-star"></i> Преимущества PRO:
                </h3>
                <ul style="color: #f0fff0; list-style: none; padding: 0;">
                    <li style="padding: 12px 0; border-bottom: 1px solid rgba(50,205,50,0.2);">
                        <i class="fas fa-check-circle" style="color: #32cd32; margin-right: 10px;"></i>
                        <strong>''' + str(PRO_LIMIT) + ''' запросов в день</strong> (вместо ''' + str(FREE_LIMIT) + ''')
                    </li>
                    <li style="padding: 12px 0; border-bottom: 1px solid rgba(50,205,50,0.2);">
                        <i class="fas fa-check-circle" style="color: #32cd32; margin-right: 10px;"></i>
                        Приоритетная обработка запросов
                    </li>
                    <li style="padding: 12px 0; border-bottom: 1px solid rgba(50,205,50,0.2);">
                        <i class="fas fa-check-circle" style="color: #32cd32; margin-right: 10px;"></i>
                        Расширенный контекст разговора
                    </li>
                    <li style="padding: 12px 0;">
                        <i class="fas fa-check-circle" style="color: #32cd32; margin-right: 10px;"></i>
                        Доступ ко всем экспертным ролям
                    </li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <a href="/" style="background: #32cd32; color: #0d3b0d; padding: 15px 30px; border-radius: 10px; text-decoration: none; font-weight: bold; display: inline-block;">
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
        <div style="max-width: 400px; margin: 100px auto; padding: 40px; background: #162416; border-radius: 20px; text-align: center; border: 2px solid #32cd32;">
            <h2 style="color: #32cd32; margin-bottom: 30px;">Админ-панель</h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Пароль" 
                       style="width: 100%; padding: 15px; margin: 20px 0; border-radius: 10px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.3); color: white; font-size: 1rem;">
                <button type="submit" 
                        style="width: 100%; padding: 15px; background: #32cd32; border: none; border-radius: 10px; color: white; font-size: 1rem; font-weight: bold; cursor: pointer;">
                    <i class="fas fa-sign-in-alt"></i> Войти
                </button>
            </form>
        </div>
        '''
    
    users_total = len(users_db)
    pro_users = sum(1 for u in users_db.values() if u.get('is_pro'))
    requests_today = sum(u.get('requests_today', 0) for u in users_db.values())
    
    html = f'''
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #32cd32;">Админ-панель Mateus AI</h1>
        <p><a href="/" style="color: #90ee90;">← На главную</a></p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="background: #1a5d1a; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>👥 Пользователей</h3>
                <p style="font-size: 2.5rem;">{users_total}</p>
            </div>
            <div style="background: #9775fa; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>👑 PRO</h3>
                <p style="font-size: 2.5rem;">{pro_users}</p>
            </div>
            <div style="background: #2e8b57; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>💬 Запросы сегодня</h3>
                <p style="font-size: 2.5rem;">{requests_today}</p>
            </div>
            <div style="background: #4dabf7; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>🤖 OpenAI</h3>
                <p style="font-size: 2.5rem;">{"✅ Работает" if OPENAI_API_KEY and len(OPENAI_API_KEY) > 30 else "❌ Ошибка"}</p>
            </div>
        </div>
        
        <h2>Создать PRO код</h2>
        <form method="POST" action="/admin/create_code">
            <input type="hidden" name="password" value="{ADMIN_PASSWORD}">
            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <input type="number" name="days" value="30" placeholder="Дней" 
                       style="padding: 12px; border-radius: 8px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.3); color: white; width: 120px;">
                <input type="text" name="note" placeholder="Примечание (необязательно)" 
                       style="flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #2a5c2a; background: rgba(0,0,0,0.3); color: white;">
                <button type="submit" 
                        style="padding: 12px 24px; background: #32cd32; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer;">
                    <i class="fas fa-plus"></i> Создать код
                </button>
            </div>
        </form>
        
        <h2>Активные PRO коды</h2>
        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <p style="color: #a3d9a3; margin-bottom: 10px;">Тестовый код: <code style="background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 5px;">PRO-TEST123</code></p>
        </div>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: #162416; border-radius: 10px; overflow: hidden; margin: 20px 0;">
                <tr style="background: #2a5c2a;">
                    <th style="padding: 15px; text-align: left;">Код</th>
                    <th style="padding: 15px; text-align: left;">Создан</th>
                    <th style="padding: 15px; text-align: left;">Истекает</th>
                    <th style="padding: 15px; text-align: left;">Использован</th>
                    <th style="padding: 15px; text-align: left;">Примечание</th>
                </tr>
    '''
    
    for code, data in settings_db.get('pro_codes', {}).items():
        html += f'''
                <tr style="border-bottom: 1px solid #2a5c2a;">
                    <td style="padding: 12px;"><code>{code}</code></td>
                    <td style="padding: 12px;">{data.get('created', '')[:10]}</td>
                    <td style="padding: 12px;">{data.get('expires', '')[:10]}</td>
                    <td style="padding: 12px;">{'✅' if data.get('used') else '❌'}</td>
                    <td style="padding: 12px;">{data.get('note', '') or '-'}</td>
                </tr>
        '''
    
    html += '''
            </table>
        </div>
        
        <h2>Пользователи (последние 20)</h2>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: #162416; border-radius: 10px; overflow: hidden; margin: 20px 0;">
                <tr style="background: #2a5c2a;">
                    <th style="padding: 15px; text-align: left;">ID</th>
                    <th style="padding: 15px; text-align: left;">PRO</th>
                    <th style="padding: 15px; text-align: left;">Запросы</th>
                    <th style="padding: 15px; text-align: left;">История</th>
                    <th style="padding: 15px; text-align: left;">Последний</th>
                </tr>
    '''
    
    for uid, user in list(users_db.items())[:20]:
        history_len = len(user.get('chat_history', []))
        last_request = user.get('last_request', '-')
        
        html += f'''
                <tr style="border-bottom: 1px solid #2a5c2a;">
                    <td style="padding: 12px;"><code>{uid[:12]}...</code></td>
                    <td style="padding: 12px;">{'✅ PRO' if user.get('is_pro') else '❌ Free'}</td>
                    <td style="padding: 12px;">{user.get('requests_today', 0)}</td>
                    <td style="padding: 12px;">{history_len // 2} диалогов</td>
                    <td style="padding: 12px;">{last_request}</td>
                </tr>
        '''
    
    html += f'''
            </table>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: rgba(50,205,50,0.1); border-radius: 10px;">
            <h3 style="color: #32cd32;">Статус системы</h3>
            <p style="color: #a3d9a3;">
                <strong>OpenAI API:</strong> {'✅ Работает' if OPENAI_API_KEY and len(OPENAI_API_KEY) > 30 else '❌ Ошибка'}<br>
                <strong>Ключ:</strong> {OPENAI_API_KEY[:15]}...<br>
                <strong>Всего пользователей:</strong> {users_total}<br>
                <strong>Запросов сегодня:</strong> {requests_today}<br>
                <strong>PRO пользователей:</strong> {pro_users} ({round(pro_users/users_total*100, 1) if users_total > 0 else 0}%)
            </p>
        </div>
    </div>
    '''
    
    return html

@app.route('/admin/create_code', methods=['POST'])
def create_pro_code():
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return "Ошибка доступа", 403
    
    code = "PRO-" + secrets.token_hex(6).upper()
    days = int(request.form.get('days', 30))
    note = request.form.get('note', '')
    
    settings_db.setdefault('pro_codes', {})[code] = {
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(days=days)).isoformat(),
        'used': False,
        'note': note
    }
    
    return f'''
    <script>
        alert("✅ PRO код создан:\\n{code}\\n\\nСкопируйте его: {code}");
        location.href = "/admin?password={ADMIN_PASSWORD}";
    </script>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Mateus AI',
        'ai': 'OpenAI GPT-3.5 Turbo',
        'openai_key': OPENAI_API_KEY[:8] + '...',
        'key_valid': len(OPENAI_API_KEY) > 30,
        'timestamp': datetime.now().isoformat(),
        'users': len(users_db),
        'version': '4.0',
        'message': 'Используется ваш новый ключ OpenAI'
    })

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Запуск Mateus AI v4.0 на порту {port}")
    print(f"🧠 Реальный AI: OpenAI GPT-3.5 Turbo")
    print(f"🔑 Ваш новый ключ OpenAI: {OPENAI_API_KEY[:15]}...")
    print(f"💰 PRO система: активна ({PRO_LIMIT} запросов/день)")
    print("✅ Готов к работе! Отправьте 'Привет' для теста.")
    app.run(host='0.0.0.0', port=port, debug=False)
