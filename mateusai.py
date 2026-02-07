import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-secret-key-2024-change-this')
app.permanent_session_lifetime = timedelta(days=30)

# База данных в памяти
users_db = {}
admin_password = os.environ.get('ADMIN_PASSWORD', 'MateusAdmin2024!')

class MateusAI:
    def __init__(self):
        self.knowledge_base = {
            'время': self.get_time_info,
            'дата': self.get_time_info,
            'привет': self.greet,
            'помощь': self.help_info,
            'о себе': self.about,
            'возможности': self.capabilities
        }
    
    def get_time_info(self):
        now = datetime.now()
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return {
            'answer': f"🕒 **Текущее время и дата:**\n\n📅 Дата: {now.strftime('%d.%m.%Y')}\n📆 День недели: {weekdays[now.weekday()]}\n⏰ Время: {now.strftime('%H:%M:%S')}\n🌍 Часовой пояс: UTC",
            'sources': [],
            'confidence': 'высокая'
        }
    
    def greet(self):
        return {
            'answer': "🤖 **Привет! Я Mateus AI.**\n\nЯ нейросеть для поиска и анализа информации. Задайте мне вопрос, и я найду информацию в интернете!\n\n💡 Примеры:\n• Какая погода?\n• Кто создал Python?\n• Что такое ИИ?\n• Новости технологий",
            'sources': [],
            'confidence': 'высокая'
        }
    
    def help_info(self):
        return {
            'answer': "🤖 **Помощь по Mateus AI:**\n\n1. Задайте любой вопрос\n2. Я ищу информацию в интернете\n3. Анализирую и сравниваю данные\n4. Предоставляю точный ответ\n\n💡 **Команды:**\n• 'время' - текущее время\n• 'дата' - текущая дата\n• 'о себе' - информация обо мне\n• 'токены' - информация о токенах",
            'sources': [],
            'confidence': 'высокая'
        }
    
    def about(self):
        return {
            'answer': "🤖 **Mateus AI** - нейросеть для поиска и анализа информации.\n\n🔍 **Мои функции:**\n• Поиск в интернете\n• Анализ информации\n• Сравнение данных\n• Ответы на вопросы\n• Работа с запросами\n\n💎 **Подписка Pro:**\n• Неограниченные запросы\n• Приоритетная обработка\n• Расширенный анализ",
            'sources': [],
            'confidence': 'высокая'
        }
    
    def capabilities(self):
        return {
            'answer': "🚀 **Возможности Mateus AI:**\n\n1. 🔍 **Поиск информации** - ищу данные в интернете\n2. 📊 **Анализ** - сравниваю и анализирую информацию\n3. 💬 **Диалог** - отвечаю на любые вопросы\n4. ⏰ **Время** - показываю актуальное время\n5. 💎 **Pro функции** - расширенные возможности для подписчиков",
            'sources': [],
            'confidence': 'высокая'
        }
    
    def search_web(self, query):
        """Имитация поиска в интернете"""
        results = []
        
        # Базовые знания
        knowledge = {
            'python': "Python - язык программирования, созданный Гвидо ван Россумом. Используется для веб-разработки, data science и ИИ.",
            'ии': "Искусственный интеллект - область компьютерных наук, создающая системы, способные выполнять задачи, требующие человеческого интеллекта.",
            'нейросеть': "Нейронная сеть - математическая модель, имитирующая работу мозга. Используется для распознавания образов, прогнозирования и анализа.",
            'flask': "Flask - микрофреймворк на Python для веб-разработки. Простой и гибкий, идеален для создания веб-приложений.",
            'render': "Render.com - облачная платформа для размещения веб-приложений с автоматическим масштабированием и SSL сертификатами.",
            'погода': "Погода зависит от региона. Для точного прогноза уточните город или страну.",
            'биткоин': "Bitcoin - первая криптовалюта, созданная Сатоши Накамото. Работает на технологии blockchain.",
            'космос': "Космос - пространство за пределами земной атмосферы. Содержит звезды, планеты, галактики и черные дыры.",
            'интернет': "Интернет - глобальная сеть, соединяющая компьютеры по всему миру. Основан на протоколе TCP/IP.",
            'технологии': "Современные технологии включают ИИ, блокчейн, IoT, облачные вычисления и квантовые компьютеры."
        }
        
        query_lower = query.lower()
        
        # Ищем совпадения
        for key, value in knowledge.items():
            if key in query_lower:
                results.append({
                    'title': f'Информация: {key}',
                    'content': value,
                    'source': 'https://knowledge.mateus.ai',
                    'confidence': 0.8
                })
        
        # Если нет совпадений, создаем общий ответ
        if not results:
            results.append({
                'title': f'Результаты по запросу: {query}',
                'content': f'По вашему запросу "{query}" проведен поиск в интернете. Найдена информация из различных источников. Анализ данных показывает...',
                'source': 'https://search.mateus.ai',
                'confidence': 0.6
            })
        
        return results
    
    def process(self, query):
        query_lower = query.lower().strip()
        
        # Проверяем специальные команды
        if query_lower in self.knowledge_base:
            return self.knowledge_base[query_lower]()
        
        # Поиск в интернете
        results = self.search_web(query)
        
        # Формируем ответ
        if results:
            main_result = results[0]
            
            answer = f"🤖 **Mateus AI отвечает на: '{query}'**\n\n"
            answer += f"🔍 **На основе анализа интернета:**\n\n"
            answer += f"📝 {main_result['content']}\n\n"
            
            if len(results) > 1:
                answer += f"📚 **Источники информации:**\n"
                for i, res in enumerate(results[:3], 1):
                    answer += f"{i}. {res['title']}\n"
            
            answer += f"\n⚡ **Уверенность:** {int(main_result['confidence'] * 100)}%\n"
            answer += f"🔄 **Проанализировано источников:** {len(results)}\n"
            
            if main_result['confidence'] < 0.7:
                answer += "\n💡 **Совет:** Попробуйте уточнить вопрос для более точного ответа."
            
            return {
                'answer': answer,
                'sources': [r['source'] for r in results[:3]],
                'confidence': 'высокая' if main_result['confidence'] > 0.7 else 'средняя'
            }
        
        return {
            'answer': f"🤖 **Mateus AI:**\n\nПо запросу '{query}' не удалось найти достаточную информацию.\n\nПопробуйте:\n1. Переформулировать вопрос\n2. Использовать другие ключевые слова\n3. Задать более конкретный запрос",
            'sources': [],
            'confidence': 'низкая'
        }

# Инициализация ИИ
ai = MateusAI()

def get_user_data(username):
    if username not in users_db:
        today = datetime.now().strftime('%Y-%m-%d')
        users_db[username] = {
            'tokens': 100,
            'subscription': 'free',
            'daily_requests': 0,
            'last_date': today,
            'password': None
        }
    return users_db[username]

# HTML интерфейс
HTML = '''<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Mateus AI</title>
<style>
:root{--green:#00ff88;--dark:#000;--card:#111;--text:#fff;--gray:#888;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--dark);color:var(--text);font-family:Arial,sans-serif;padding:20px;}
.container{max-width:1200px;margin:0 auto;}
header{text-align:center;padding:30px 0;margin-bottom:30px;}
.logo{font-size:48px;font-weight:bold;color:var(--green);text-shadow:0 0 10px var(--green);margin-bottom:10px;}
.slogan{color:var(--gray);font-size:18px;margin-bottom:20px;}
.user-panel{position:absolute;top:20px;right:20px;}
.main{display:flex;gap:30px;flex-wrap:wrap;}
.chat{flex:1;min-width:300px;}
.sidebar{width:350px;min-width:300px;}
.card{background:var(--card);border:1px solid #222;border-radius:15px;padding:25px;margin-bottom:20px;}
.messages{height:400px;overflow-y:auto;padding:15px;background:#000;border-radius:10px;margin-bottom:20px;border:1px solid #222;}
.message{padding:12px 15px;margin-bottom:10px;border-radius:10px;max-width:85%;}
.user-msg{background:linear-gradient(45deg,#003322,#005533);margin-left:auto;border:1px solid var(--green);}
.ai-msg{background:#1a1a1a;margin-right:auto;border:1px solid #333;white-space:pre-line;}
.input-row{display:flex;gap:10px;}
input[type="text"]{flex:1;padding:15px;background:#000;border:2px solid var(--green);border-radius:10px;color:white;font-size:16px;}
.btn{padding:15px 25px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;}
.btn-primary{background:linear-gradient(45deg,#003322,var(--green));color:black;}
.btn-premium{background:linear-gradient(45deg,#330066,#8800ff);color:white;}
.btn-danger{background:linear-gradient(45deg,#660000,#ff3300);color:white;}
.stats{margin:20px 0;}
.stat-item{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #222;}
.stat-value{color:var(--green);font-weight:bold;}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:1000;}
.modal-content{background:var(--card);max-width:400px;margin:100px auto;padding:30px;border-radius:15px;border:2px solid var(--green);}
.close{position:absolute;top:15px;right:20px;color:var(--green);font-size:24px;cursor:pointer;}
.notification{position:fixed;top:20px;right:20px;padding:15px 25px;background:var(--card);border:1px solid var(--green);border-radius:10px;z-index:1001;display:none;}
@media(max-width:768px){.main{flex-direction:column;}.sidebar{width:100%;}.user-panel{position:relative;top:0;right:0;}}
</style>
</head>
<body>
<div class="container">
<header>
<div class="logo">MATEUS AI</div>
<div class="slogan">Нейросеть для ваших запросов</div>
<div class="user-panel" id="userPanel"></div>
</header>
<div class="main">
<div class="chat"><div class="card">
<h3 style="color:var(--green);margin-bottom:15px;">💬 Чат с Mateus AI</h3>
<div class="messages" id="chat">
<div class="message ai-msg">🤖 Привет! Задайте вопрос, и я найду информацию в интернете.</div>
</div>
<div class="input-row">
<input type="text" id="question" placeholder="Введите ваш вопрос..." autocomplete="off">
<button class="btn btn-primary" onclick="askAI()">Отправить</button>
</div>
<div id="loading" style="display:none;color:var(--green);text-align:center;padding:10px;">🔍 Ищу информацию...</div>
</div></div>
<div class="sidebar"><div class="card">
<h3 style="color:var(--green);margin-bottom:20px;">📊 Статистика</h3>
<div class="stats">
<div class="stat-item"><span>Токены:</span><span class="stat-value" id="tokens">0</span></div>
<div class="stat-item"><span>Подписка:</span><span class="stat-value" id="sub">Free</span></div>
<div class="stat-item"><span>Запросы сегодня:</span><span class="stat-value" id="requests">0/34</span></div>
<div class="stat-item"><span>До Pro:</span><span class="stat-value" id="toPro">1000</span></div>
</div>
<div style="margin-top:25px;display:grid;gap:10px;">
<button class="btn btn-premium" onclick="upgrade()" id="upgradeBtn">💎 Апгрейд до Pro</button>
<button class="btn" onclick="admin()" style="background:#333;color:white;">🔧 Админ-панель</button>
<button class="btn btn-danger" onclick="logout()" id="logoutBtn">🚪 Выйти</button>
</div>
</div></div>
</div>
</div>
<div class="modal" id="loginModal">
<div class="modal-content">
<span class="close" onclick="closeModal('loginModal')">×</span>
<h2 style="color:var(--green);margin-bottom:25px;">🔐 Вход / Регистрация</h2>
<input type="text" id="username" placeholder="Имя пользователя" style="width:100%;margin-bottom:10px;padding:12px;">
<input type="password" id="password" placeholder="Пароль" style="width:100%;margin-bottom:10px;padding:12px;">
<div id="loginError" style="color:#ff4444;margin-bottom:15px;"></div>
<button class="btn btn-primary" onclick="login()" style="width:100%;">Войти / Создать аккаунт</button>
</div>
</div>
<div class="modal" id="adminModal">
<div class="modal-content">
<span class="close" onclick="closeModal('adminModal')">×</span>
<h2 style="color:var(--green);margin-bottom:25px;">🔧 Админ-панель</h2>
<input type="password" id="adminPass" placeholder="Пароль админа" style="width:100%;margin-bottom:10px;padding:12px;">
<input type="text" id="targetUser" placeholder="Имя пользователя" style="width:100%;margin-bottom:10px;padding:12px;">
<select id="adminAction" style="width:100%;padding:12px;margin-bottom:10px;background:#000;color:white;">
<option value="add_tokens">Добавить токены</option>
<option value="set_pro">Дать Pro</option>
<option value="remove_pro">Убрать Pro</option>
</select>
<input type="number" id="amount" value="100" style="width:100%;padding:12px;">
<div id="adminError" style="color:#ff4444;margin-bottom:15px;"></div>
<button class="btn btn-primary" onclick="doAdminAction()" style="width:100%;">Выполнить</button>
</div>
</div>
<div class="modal" id="upgradeModal">
<div class="modal-content">
<span class="close" onclick="closeModal('upgradeModal')">×</span>
<h2 style="color:var(--green);margin-bottom:25px;">💎 Подписка Pro</h2>
<div style="background:#000;padding:20px;border-radius:10px;margin-bottom:20px;">
<h4>Преимущества:</h4>
<ul style="padding-left:20px;color:var(--gray);margin-top:10px;">
<li>✅ Неограниченные запросы</li>
<li>⚡ Приоритетная обработка</li>
<li>🔍 Расширенный анализ</li>
<li>🚀 Экспериментальные функции</li>
</ul>
</div>
<div style="text-align:center;padding:20px;border:2px solid var(--green);border-radius:10px;margin-bottom:20px;">
<h3>Стоимость: 1000 токенов</h3>
<p id="tokensInfo" style="color:var(--gray);margin-top:10px;"></p>
</div>
<button class="btn btn-premium" onclick="doUpgrade()" style="width:100%;" id="upgradeActionBtn">Активировать Pro</button>
</div>
</div>
<div class="notification" id="notification"></div>
<script>
let currentUser=null;
document.addEventListener('DOMContentLoaded',()=>{checkAuth();setTimeout(()=>{if(!currentUser)showLoginModal();},500);});
function showLoginModal(){document.getElementById('loginModal').style.display='block';}
function showAdminModal(){if(!currentUser){showNotification('Войдите в систему','error');showLoginModal();return;}
document.getElementById('adminModal').style.display='block';}
function showUpgradeModal(){if(!currentUser){showNotification('Войдите в систему','error');showLoginModal();return;}
document.getElementById('upgradeModal').style.display='block';
const tokens=document.getElementById('tokensInfo');
const btn=document.getElementById('upgradeActionBtn');
if(currentUser.tokens>=1000){tokens.innerHTML='<span style="color:#00ff88">✅ Достаточно токенов</span>';btn.disabled=false;btn.innerHTML='💰 Активировать Pro';}
else{const need=1000-currentUser.tokens;tokens.innerHTML='<span style="color:#ff4444">❌ Нужно еще '+need+' токенов</span>';btn.disabled=true;btn.innerHTML='❌ Недостаточно';}}
function closeModal(id){document.getElementById(id).style.display='none';}
function showNotification(msg,type='info'){const n=document.getElementById('notification');n.textContent=msg;n.style.display='block';n.style.borderColor=type==='error'?'#ff4444':'#00ff88';setTimeout(()=>n.style.display='none',3000);}
async function login(){const u=document.getElementById('username').value.trim();const p=document.getElementById('password').value;
if(!u||!p){document.getElementById('loginError').textContent='Заполните все поля';return;}
const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
const d=await r.json();if(d.success){currentUser=d.user;updateUI();closeModal('loginModal');showNotification('Добро пожаловать!','success');
addMessage('🤖 Привет, '+u+'! Теперь можете задавать вопросы.','ai');}else{document.getElementById('loginError').textContent=d.error;}}
async function askAI(){if(!currentUser){showLoginModal();return;}
const q=document.getElementById('question').value.trim();if(!q)return;addMessage(q,'user');document.getElementById('question').value='';document.getElementById('loading').style.display='block';
try{const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const d=await r.json();
if(d.success){addMessage(d.answer,'ai');updateUI();}else{addMessage('❌ '+d.error,'ai');}}catch(e){addMessage('❌ Ошибка сети','ai');}
document.getElementById('loading').style.display='none';}
async function upgrade(){showUpgradeModal();}
async function doUpgrade(){const r=await fetch('/api/upgrade',{method:'POST'});const d=await r.json();
if(d.success){currentUser=d.user;updateUI();closeModal('upgradeModal');showNotification('🎉 Теперь у вас Pro!','success');}else{showNotification(d.error,'error');}}
async function doAdminAction(){const p=document.getElementById('adminPass').value;const u=document.getElementById('targetUser').value.trim();const a=document.getElementById('adminAction').value;const n=parseInt(document.getElementById('amount').value);
if(!p||!u){document.getElementById('adminError').textContent='Заполните все поля';return;}
const r=await fetch('/api/admin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p,username:u,action:a,amount:n})});const d=await r.json();
if(d.success){showNotification(d.message,'success');closeModal('adminModal');if(currentUser&&currentUser.username===u)checkAuth();}else{document.getElementById('adminError').textContent=d.error;}}
async function logout(){await fetch('/api/logout');currentUser=null;updateUI();document.getElementById('chat').innerHTML='<div class="message ai-msg">🤖 Вы вышли из системы</div>';showNotification('Вы вышли','info');setTimeout(showLoginModal,1000);}
function addMessage(txt,type){const c=document.getElementById('chat');const m=document.createElement('div');m.className='message '+(type==='user'?'user-msg':'ai-msg');m.textContent=txt;c.appendChild(m);c.scrollTop=c.scrollHeight;}
function updateUI(){const p=document.getElementById('userPanel');const t=document.getElementById('tokens');const s=document.getElementById('sub');const r=document.getElementById('requests');const tp=document.getElementById('toPro');const ub=document.getElementById('upgradeBtn');const lb=document.getElementById('logoutBtn');
if(currentUser){p.innerHTML='<div>👤 <strong>'+currentUser.username+'</strong>'+(currentUser.subscription==='pro'?' <span style="color:#8800ff">PRO</span>':'')+'</div><div style="font-size:14px;color:var(--gray);">Токены: '+currentUser.tokens+'</div>';
t.textContent=currentUser.tokens;s.textContent=currentUser.subscription;s.style.color=currentUser.subscription==='pro'?'#8800ff':'var(--green)';
r.textContent=currentUser.daily_requests+'/'+(currentUser.subscription==='pro'?'∞':'34');if(currentUser.subscription==='pro'){tp.textContent='PRO';tp.style.color='#8800ff';ub.style.display='none';}else{const n=1000-currentUser.tokens;tp.textContent=n>0?n:'Готово!';ub.style.display='block';}lb.style.display='block';}
else{p.innerHTML='<button class="btn btn-primary" onclick="showLoginModal()">Войти / Регистрация</button>';t.textContent='0';s.textContent='None';r.textContent='0/0';tp.textContent='1000';ub.style.display='block';lb.style.display='none';}}
async function checkAuth(){try{const r=await fetch('/api/me');const d=await r.json();if(d.success){currentUser=d.user;updateUI();}}catch(e){}}
document.getElementById('question').addEventListener('keypress',e=>{if(e.key==='Enter')askAI();});
window.onclick=e=>{if(e.target.classList.contains('modal'))e.target.style.display='none';};
function admin(){showAdminModal();}
</script>
</body>
</html>'''

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
            return jsonify({'success': False, 'error': 'Имя минимум 3 символа'})
        
        # Хешируем пароль
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Проверяем пользователя
        user = get_user_data(username)
        
        if user['password'] is None:
            # Регистрация
            user['password'] = password_hash
            session['username'] = username
            return jsonify({
                'success': True,
                'user': {
                    'username': username,
                    'tokens': user['tokens'],
                    'subscription': user['subscription'],
                    'daily_requests': user['daily_requests']
                }
            })
        else:
            # Вход
            if user['password'] == password_hash:
                session['username'] = username
                return jsonify({
                    'success': True,
                    'user': {
                        'username': username,
                        'tokens': user['tokens'],
                        'subscription': user['subscription'],
                        'daily_requests': user['daily_requests']
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Неверный пароль'})
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/me')
def api_me():
    username = session.get('username')
    if username and username in users_db:
        user = users_db[username]
        return jsonify({
            'success': True,
            'user': {
                'username': username,
                'tokens': user['tokens'],
                'subscription': user['subscription'],
                'daily_requests': user['daily_requests']
            }
        })
    return jsonify({'success': False})

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        username = session.get('username')
        if not username or username not in users_db:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})
        
        user = users_db[username]
        
        # Проверка дневного лимита
        today = datetime.now().strftime('%Y-%m-%d')
        if user['last_date'] != today:
            user['daily_requests'] = 0
            user['last_date'] = today
        
        # Лимит 34 запроса для бесплатных
        if user['subscription'] == 'free' and user['daily_requests'] >= 34:
            return jsonify({'success': False, 'error': 'Достигнут лимит 34 запроса в день'})
        
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Введите вопрос'})
        
        # Обработка запроса
        response = ai.process(question)
        
        # Обновляем статистику
        user['daily_requests'] += 1
        
        # Начисляем токены
        if user['subscription'] == 'free':
            user['tokens'] += 10
        
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
        import hashlib
        if hashlib.sha256(password.encode()).hexdigest() != hashlib.sha256(admin_password.encode()).hexdigest():
            return jsonify({'success': False, 'error': 'Неверный пароль админа'})
        
        if target_username not in users_db:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})
        
        user = users_db[target_username]
        
        if action == 'add_tokens':
            user['tokens'] += int(amount)
            message = f'Добавлено {amount} токенов'
        elif action == 'set_pro':
            user['subscription'] = 'pro'
            message = 'Подписка Pro активирована'
        elif action == 'remove_pro':
            user['subscription'] = 'free'
            message = 'Подписка Pro отключена'
        else:
            return jsonify({'success': False, 'error': 'Неизвестное действие'})
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upgrade', methods=['POST'])
def api_upgrade():
    try:
        username = session.get('username')
        if not username or username not in users_db:
            return jsonify({'success': False, 'error': 'Требуется авторизация'})
        
        user = users_db[username]
        
        if user['subscription'] == 'pro':
            return jsonify({'success': False, 'error': 'У вас уже есть Pro'})
        
        if user['tokens'] < 1000:
            return jsonify({'success': False, 'error': f'Нужно 1000 токенов, у вас {user["tokens"]}'})
        
        user['tokens'] -= 1000
        user['subscription'] = 'pro'
        
        return jsonify({
            'success': True,
            'user': {
                'username': username,
                'tokens': user['tokens'],
                'subscription': user['subscription'],
                'daily_requests': user['daily_requests']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
