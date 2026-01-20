"""
Mateus AI - Полная версия с системой токенов, OAuth DonationAlerts и магазином
"""

import os
import uuid
import secrets
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import requests
import json
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ==================== КОНФИГУРАЦИЯ ====================
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
DONATIONALERTS_CLIENT_ID = os.environ.get('DONATIONALERTS_CLIENT_ID')
DONATIONALERTS_CLIENT_SECRET = os.environ.get('DONATIONALERTS_CLIENT_SECRET')
DONATIONALERTS_REDIRECT_URI = os.environ.get('DONATIONALERTS_REDIRECT_URI', 'https://mateus-ai.onrender.com/auth/donationalerts/callback')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123')
TELEGRAM_SUPPORT = "@MateuKras_new"

# Система токенов
FREE_LIMIT = 10
PRO_LIMIT = 1000
TOKENS_PER_HALF_HOUR = 150  # +150 токенов за каждые 30 минут общения
PRO_PRICE_TOKENS = 1000     # 1000 токенов = PRO подписка
TOKEN_VALUE = 1             # 1 токен = 1 рубль

# ==================== БАЗА ДАННЫХ ====================

def get_db():
    """Подключение к базе данных"""
    db_path = os.path.join(os.path.dirname(__file__), 'data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Пользователи
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        requests_today INTEGER DEFAULT 0,
        last_request_date TEXT,
        is_pro BOOLEAN DEFAULT 0,
        pro_expires TEXT,
        tokens INTEGER DEFAULT 0,
        total_tokens_earned INTEGER DEFAULT 0,
        total_tokens_spent INTEGER DEFAULT 0,
        last_token_bonus TEXT,
        chat_start_time TEXT,
        total_chat_minutes INTEGER DEFAULT 0,
        da_user_id TEXT,
        da_access_token TEXT,
        da_refresh_token TEXT,
        da_username TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Транзакции токенов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS token_transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        type TEXT, -- 'earn', 'spend', 'purchase', 'bonus', 'pro_purchase', 'reward'
        amount INTEGER,
        description TEXT,
        balance_after INTEGER,
        created_at TEXT
    )
    ''')
    
    # PRO коды (теперь для админа)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pro_codes (
        code TEXT PRIMARY KEY,
        created_at TEXT,
        expires_at TEXT,
        used BOOLEAN DEFAULT 0,
        used_by TEXT,
        used_at TEXT,
        note TEXT
    )
    ''')
    
    # Донаты через DonationAlerts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donations (
        id TEXT PRIMARY KEY,
        da_donation_id TEXT,
        user_id TEXT,
        username TEXT,
        amount REAL,
        currency TEXT,
        message TEXT,
        tokens_granted INTEGER,
        is_processed BOOLEAN DEFAULT 0,
        created_at TEXT
    )
    ''')
    
    # Настройки магазина
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shop_items (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        token_price INTEGER,
        is_active BOOLEAN DEFAULT 1,
        created_at TEXT
    )
    ''')
    
    # Добавляем стандартные товары в магазин
    cursor.execute('''
    INSERT OR IGNORE INTO shop_items (id, name, description, token_price, is_active, created_at)
    VALUES 
        ('pro_1month', 'PRO на 1 месяц', 'PRO доступ на 30 дней', 1000, 1, ?),
        ('tokens_100', '100 токенов', 'Дополнительные 100 токенов', 100, 1, ?),
        ('tokens_500', '500 токенов', 'Дополнительные 500 токенов', 500, 1, ?),
        ('tokens_1000', '1000 токенов', 'Дополнительные 1000 токенов', 1000, 1, ?)
    ''', (datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

# Инициализируем БД при старте
init_db()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_user_id():
    """Получить или создать ID пользователя"""
    user_id = session.get('user_id')
    session_id = session.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    conn = get_db()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if cursor.fetchone():
            conn.close()
            return user_id
    
    # Создаем нового пользователя
    user_id = str(uuid.uuid4())
    session['user_id'] = user_id
    
    # Начисляем стартовые 100 токенов
    cursor.execute('''
        INSERT INTO users (id, session_id, tokens, created_at)
        VALUES (?, ?, 100, ?)
    ''', (user_id, session_id, datetime.now().isoformat()))
    
    # Записываем транзакцию
    transaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO token_transactions (id, user_id, type, amount, description, balance_after, created_at)
        VALUES (?, ?, 'bonus', 100, 'Стартовый бонус', 100, ?)
    ''', (transaction_id, user_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return user_id

def get_user_data(user_id):
    """Получить данные пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_requests(user_id):
    """Обновить счетчик запросов"""
    today = datetime.now().date().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT last_request_date, requests_today FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        last_date = user['last_request_date']
        requests_today = user['requests_today'] or 0
        
        if last_date != today:
            requests_today = 0
        
        requests_today += 1
        
        cursor.execute('''
            UPDATE users 
            SET requests_today = ?, last_request_date = ?
            WHERE id = ?
        ''', (requests_today, today, user_id))
        
        conn.commit()
    
    conn.close()
    return requests_today

def check_and_award_tokens(user_id):
    """Проверить и начислить токены за время в чате"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT chat_start_time, total_chat_minutes FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return 0
    
    chat_start_time = user['chat_start_time']
    total_minutes = user['total_chat_minutes'] or 0
    
    if not chat_start_time:
        # Начинаем отсчет времени
        cursor.execute('UPDATE users SET chat_start_time = ? WHERE id = ?', 
                      (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        return 0
    
    # Вычисляем разницу во времени
    start_time = datetime.fromisoformat(chat_start_time)
    now = datetime.now()
    delta_minutes = int((now - start_time).total_seconds() / 60)
    
    # Начисляем токены каждые 30 минут
    bonus_tokens = 0
    if delta_minutes >= 30:
        half_hours = delta_minutes // 30
        bonus_tokens = half_hours * TOKENS_PER_HALF_HOUR
        
        if bonus_tokens > 0:
            # Обновляем токены пользователя
            cursor.execute('SELECT tokens FROM users WHERE id = ?', (user_id,))
            current_tokens = cursor.fetchone()['tokens'] or 0
            new_tokens = current_tokens + bonus_tokens
            
            cursor.execute('''
                UPDATE users 
                SET tokens = ?, 
                    total_tokens_earned = total_tokens_earned + ?,
                    total_chat_minutes = total_chat_minutes + ?,
                    chat_start_time = ?
                WHERE id = ?
            ''', (new_tokens, bonus_tokens, delta_minutes, now.isoformat(), user_id))
            
            # Записываем транзакцию
            transaction_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO token_transactions (id, user_id, type, amount, description, balance_after, created_at)
                VALUES (?, ?, 'reward', ?, 'Награда за время в чате', ?, ?)
            ''', (transaction_id, user_id, bonus_tokens, new_tokens, now.isoformat()))
            
            conn.commit()
    
    conn.close()
    return bonus_tokens

def check_request_limit(user_id):
    """Проверить лимит запросов"""
    user = get_user_data(user_id)
    if not user:
        return False, FREE_LIMIT, 0, 0
    
    today = datetime.now().date().isoformat()
    last_date = user['last_request_date']
    requests_today = user['requests_today'] or 0
    
    # Сброс если новый день
    if last_date != today:
        requests_today = 0
        conn = get_db()
        conn.execute('UPDATE users SET requests_today = 0, last_request_date = ? WHERE id = ?', 
                    (today, user_id))
        conn.commit()
        conn.close()
    
    # Определяем лимит
    is_pro = user['is_pro']
    limit = PRO_LIMIT if is_pro else FREE_LIMIT
    remaining = limit - requests_today
    
    return requests_today < limit, limit, requests_today, remaining

def spend_tokens(user_id, amount, description):
    """Списать токены у пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT tokens FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or user['tokens'] < amount:
        conn.close()
        return False, "Недостаточно токенов"
    
    new_balance = user['tokens'] - amount
    
    cursor.execute('''
        UPDATE users 
        SET tokens = ?, total_tokens_spent = total_tokens_spent + ?
        WHERE id = ?
    ''', (new_balance, amount, user_id))
    
    # Записываем транзакцию
    transaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO token_transactions (id, user_id, type, amount, description, balance_after, created_at)
        VALUES (?, ?, 'spend', ?, ?, ?, ?)
    ''', (transaction_id, user_id, amount, description, new_balance, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return True, new_balance

def add_tokens(user_id, amount, description, trans_type='purchase'):
    """Добавить токены пользователю"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT tokens FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "Пользователь не найден"
    
    new_balance = user['tokens'] + amount
    
    if trans_type == 'purchase':
        cursor.execute('''
            UPDATE users 
            SET tokens = ?, total_tokens_earned = total_tokens_earned + ?
            WHERE id = ?
        ''', (new_balance, amount, user_id))
    else:
        cursor.execute('''
            UPDATE users SET tokens = ? WHERE id = ?
        ''', (new_balance, user_id))
    
    # Записываем транзакцию
    transaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO token_transactions (id, user_id, type, amount, description, balance_after, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, trans_type, amount, description, new_balance, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return True, new_balance

def activate_pro_with_tokens(user_id):
    """Активировать PRO за токены"""
    user = get_user_data(user_id)
    
    if not user:
        return False, "Пользователь не найден"
    
    if user['is_pro']:
        return False, "У вас уже активирована PRO подписка"
    
    # Списание токенов
    success, message = spend_tokens(user_id, PRO_PRICE_TOKENS, "Покупка PRO подписки")
    
    if not success:
        return False, message
    
    # Активация PRO
    expires = (datetime.now() + timedelta(days=30)).isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET is_pro = 1, pro_expires = ?
        WHERE id = ?
    ''', (expires, user_id))
    
    # Записываем транзакцию
    transaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO token_transactions (id, user_id, type, amount, description, balance_after, created_at)
        VALUES (?, ?, 'pro_purchase', ?, 'Активация PRO подписки', ?, ?)
    ''', (transaction_id, user_id, PRO_PRICE_TOKENS, message, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return True, f"PRO подписка активирована на 30 дней! Истекает: {expires[:10]}"

# ==================== DONATION ALERTS OAuth ====================

@app.route('/auth/donationalerts')
def auth_donationalerts():
    """Перенаправление на авторизацию DonationAlerts"""
    auth_url = "https://www.donationalerts.com/oauth/authorize"
    params = {
        'client_id': DONATIONALERTS_CLIENT_ID,
        'redirect_uri': DONATIONALERTS_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'oauth-donation-index oauth-user-show oauth-donation-subscribe'
    }
    auth_url_with_params = f"{auth_url}?{'&'.join([f'{k}={v}' for k,v in params.items()])}"
    return redirect(auth_url_with_params)

@app.route('/auth/donationalerts/callback')
def auth_donationalerts_callback():
    """Обработка callback от DonationAlerts"""
    code = request.args.get('code')
    if not code:
        return "Ошибка авторизации: нет кода", 400
    
    try:
        # Получаем access token
        token_url = "https://www.donationalerts.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': DONATIONALERTS_CLIENT_ID,
            'client_secret': DONATIONALERTS_CLIENT_SECRET,
            'redirect_uri': DONATIONALERTS_REDIRECT_URI,
            'code': code
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        if response.status_code != 200:
            return f"Ошибка получения токена: {response.text}", 400
        
        token_data = response.json()
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
        
        # Получаем информацию о пользователе
        user_url = "https://www.donationalerts.com/api/v1/user/oauth"
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_url, headers=headers, timeout=10)
        
        if user_response.status_code != 200:
            return "Ошибка получения данных пользователя", 400
        
        user_data = user_response.json()
        da_user_id = user_data['data']['id']
        da_username = user_data['data']['name']
        
        # Сохраняем данные пользователя
        user_id = get_user_id()
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET da_user_id = ?, da_access_token = ?, da_refresh_token = ?, da_username = ?
            WHERE id = ?
        ''', (da_user_id, access_token, refresh_token, da_username, user_id))
        
        conn.commit()
        conn.close()
        
        session['da_connected'] = True
        session['da_username'] = da_username
        
        return redirect(url_for('index'))
        
    except Exception as e:
        return f"Ошибка авторизации: {str(e)}", 500

def check_donationalerts_donations(user_id):
    """Проверить новые донаты через DonationAlerts"""
    if not DONATIONALERTS_CLIENT_ID:
        return []
    
    user = get_user_data(user_id)
    if not user or not user['da_access_token']:
        return []
    
    try:
        # Получаем донаты пользователя
        donations_url = "https://www.donationalerts.com/api/v1/alerts/donations"
        headers = {'Authorization': f'Bearer {user["da_access_token"]}'}
        
        response = requests.get(donations_url, headers=headers, params={'page': 1}, timeout=10)
        if response.status_code != 200:
            return []
        
        donations_data = response.json()
        new_donations = []
        
        conn = get_db()
        cursor = conn.cursor()
        
        for donation in donations_data.get('data', []):
            donation_id = donation.get('id')
            
            # Проверяем, не обрабатывали ли мы уже этот донат
            cursor.execute('SELECT id FROM donations WHERE da_donation_id = ?', (donation_id,))
            if cursor.fetchone():
                continue
            
            amount = donation.get('amount')
            currency = donation.get('currency')
            message = donation.get('message', '')
            username = donation.get('username', '')
            created_at = donation.get('created_at')
            
            # Начисляем токены (1 рубль = 1 токен)
            tokens_granted = int(amount) if currency == 'RUB' else 0
            
            # Сохраняем донат
            db_donation_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO donations (id, da_donation_id, user_id, username, amount, currency, message, tokens_granted, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (db_donation_id, donation_id, user_id, username, amount, currency, message, tokens_granted, created_at))
            
            # Начисляем токены
            if tokens_granted > 0:
                add_tokens(user_id, tokens_granted, f"Донат от {username}: {message}")
            
            new_donations.append({
                'username': username,
                'amount': amount,
                'currency': currency,
                'message': message,
                'tokens': tokens_granted
            })
        
        conn.commit()
        conn.close()
        return new_donations
        
    except Exception as e:
        print(f"Ошибка проверки донатов: {e}")
        return []

# ==================== OPENAI ИНТЕГРАЦИЯ ====================

def get_ai_response(message, role='assistant'):
    """Получить ответ от OpenAI/DeepSeek"""
    
    # Системные промпты
    role_prompts = {
        'assistant': "Ты - полезный AI ассистент Mateus. Отвечай вежливо и информативно.",
        'programmer': "Ты - опытный программист-консультант. Помогай с кодом, объясняй концепции, предлагай решения.",
        'teacher': "Ты - терпеливый учитель. Объясняй сложные темы простым языком, приводи примеры."
    }
    
    system_content = role_prompts.get(role, role_prompts['assistant'])
    
    try:
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message}
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"⚠️ Ошибка AI API: {response.status_code}"
            
    except Exception as e:
        return f"⚠️ Ошибка соединения с AI: {str(e)}"

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
            --purple: #9775fa; --red: #ff6b6b; --orange: #ffa94d;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            padding: 40px 30px;
            background: linear-gradient(135deg, var(--primary), var(--dark));
            border-radius: 20px;
            margin-bottom: 40px;
            border: 2px solid var(--accent);
            position: relative;
        }
        .logo {
            font-size: 3.5rem;
            color: var(--light);
            margin-bottom: 10px;
        }
        .title {
            font-size: 2.8rem;
            background: linear-gradient(45deg, var(--light), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
            font-weight: 700;
        }
        .main-content {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 30px;
        }
        @media (max-width: 1100px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        .card {
            background: var(--card);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        .btn {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            text-decoration: none;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(46, 139, 87, 0.4);
        }
        .btn-gold {
            background: linear-gradient(135deg, var(--gold), #ffcc00);
            color: #333;
        }
        .btn-purple {
            background: linear-gradient(135deg, var(--purple), #7950f2);
        }
        .btn-orange {
            background: linear-gradient(135deg, var(--orange), #ff922b);
        }
        .chat-messages {
            height: 500px;
            overflow-y: auto;
            margin-bottom: 25px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            border: 1px solid var(--border);
            scroll-behavior: smooth;
        }
        .message {
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 12px;
            max-width: 85%;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            margin-left: auto;
            color: white;
            border-bottom-right-radius: 5px;
        }
        .ai-message {
            background: rgba(46, 139, 87, 0.15);
            border: 1px solid var(--border);
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        .chat-input {
            display: flex;
            gap: 15px;
        }
        .chat-input input {
            flex: 1;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .chat-input input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(50, 205, 50, 0.1);
        }
        .footer {
            text-align: center;
            padding: 30px;
            color: var(--muted);
            border-top: 1px solid var(--border);
            margin-top: 40px;
            font-size: 0.9rem;
        }
        .badge {
            display: inline-block;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 10px;
        }
        .badge-pro {
            background: var(--gold);
            color: #333;
        }
        .badge-free {
            background: var(--purple);
            color: white;
        }
        .badge-token {
            background: var(--orange);
            color: #333;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .token-display {
            font-size: 2rem;
            font-weight: bold;
            color: var(--orange);
            text-align: center;
            margin: 15px 0;
        }
        .shop-item {
            background: rgba(151, 117, 250, 0.1);
            border: 1px solid var(--purple);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: transform 0.3s;
        }
        .shop-item:hover {
            transform: translateY(-5px);
            background: rgba(151, 117, 250, 0.2);
        }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--primary);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            border: 2px solid var(--accent);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div id="notification" class="notification" style="display: none;"></div>
    
    <div class="container">
        {{ header|safe }}
        <div class="main-content">
            {{ sidebar|safe }}
            {{ content|safe }}
        </div>
        {{ footer|safe }}
    </div>
    
    <script>
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.display = 'block';
            notification.style.background = type === 'success' 
                ? 'linear-gradient(135deg, #1a5d1a, #2e8b57)' 
                : 'linear-gradient(135deg, #dc3545, #c82333)';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 5000);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.focus();
            }
            
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // Проверка бонусов за время
            checkTimeBonus();
        });
        
        function checkTimeBonus() {
            fetch('/check_time_bonus')
                .then(r => r.json())
                .then(data => {
                    if (data.bonus > 0) {
                        showNotification(`🎉 +${data.bonus} токенов за время в чате!`, 'success');
                        updateTokenDisplay(data.new_balance);
                    }
                });
        }
        
        function updateTokenDisplay(balance) {
            const tokenDisplay = document.querySelector('.token-display');
            if (tokenDisplay) {
                tokenDisplay.innerHTML = `${balance} <i class="fas fa-coins"></i>`;
            }
        }
        
        window.sendMessage = function() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            const btn = document.querySelector('.chat-input .btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loader"></span>';
            btn.disabled = true;
            input.disabled = true;
            
            addMessage('user', message);
            input.value = '';
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    addMessage('ai', data.response);
                    // Обновляем статистику
                    if (data.stats) {
                        updateStats(data.stats);
                    }
                } else {
                    addMessage('ai', '<div style="color: var(--red); padding: 10px; background: rgba(255,107,107,0.1); border-radius: 8px;">' + data.error + '</div>');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage('ai', '<div style="color: var(--red);">Ошибка сети. Попробуйте позже.</div>');
            })
            .finally(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                input.disabled = false;
                input.focus();
            });
        };
        
        document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        window.buyProWithTokens = function() {
            if (!confirm('Купить PRO подписку за 1000 токенов?')) return;
            
            fetch('/buy_pro_with_tokens', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(() => location.reload(), 2000);
                } else {
                    showNotification(data.message, 'error');
                }
            });
        };
        
        window.buyShopItem = function(itemId, itemName, price) {
            if (!confirm(`Купить "${itemName}" за ${price} токенов?`)) return;
            
            fetch('/buy_shop_item', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({item_id: itemId})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    updateTokenDisplay(data.new_balance);
                    if (data.reload) {
                        setTimeout(() => location.reload(), 1500);
                    }
                } else {
                    showNotification(data.message, 'error');
                }
            });
        };
        
        window.checkDonations = function() {
            fetch('/check_donations')
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.new_donations > 0) {
                        showNotification(`💰 Получено ${data.new_donations} новых донатов!`, 'success');
                        updateTokenDisplay(data.new_balance);
                    }
                });
        };
        
        function addMessage(sender, text) {
            const chat = document.getElementById('chatMessages');
            if (!chat) return;
            
            const div = document.createElement('div');
            div.className = 'message ' + sender + '-message';
            div.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 8px; display: flex; align-items: center; gap: 10px;">
                    ${sender === 'user' ? '<i class="fas fa-user"></i> Вы' : '<i class="fas fa-robot"></i> Mateus AI'}
                    <span style="font-size: 0.8rem; opacity: 0.7; margin-left: auto;">
                        ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                </div>
                <div>${text}</div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function updateStats(stats) {
            // Обновляем отображение токенов
            const tokenDisplay = document.querySelector('.token-display');
            if (tokenDisplay && stats.tokens !== undefined) {
                tokenDisplay.innerHTML = `${stats.tokens} <i class="fas fa-coins"></i>`;
            }
            
            // Обновляем лимиты
            const limitElement = document.querySelector('.limit-display');
            if (limitElement && stats.usage) {
                limitElement.innerHTML = `${stats.usage.used}/${stats.usage.limit}`;
            }
        }
        
        window.selectRole = function(role) {
            fetch('/set_role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role: role})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const roleNames = {
                        'assistant': 'Ассистент',
                        'programmer': 'Программист',
                        'teacher': 'Учитель'
                    };
                    showNotification(`Роль "${roleNames[role]}" выбрана!`, 'success');
                }
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

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    user_id = get_user_id()
    user = get_user_data(user_id)
    
    # Проверяем и начисляем бонусы за время
    bonus_tokens = check_and_award_tokens(user_id)
    
    # Проверяем донаты
    new_donations = []
    if user and user['da_access_token']:
        new_donations = check_donationalerts_donations(user_id)
    
    can_request, limit, used, remaining = check_request_limit(user_id)
    
    # Получаем историю транзакций
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM token_transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    ''', (user_id,))
    recent_transactions = cursor.fetchall()
    
    # Получаем товары из магазина
    cursor.execute('SELECT * FROM shop_items WHERE is_active = 1 ORDER BY token_price')
    shop_items = cursor.fetchall()
    conn.close()
    
    # Статистика пользователя
    tokens = user['tokens'] if user else 100
    is_pro = user['is_pro'] if user else False
    
    header = f'''
    <div class="header">
        <div style="position: absolute; top: 20px; right: 20px; display: flex; gap: 15px; align-items: center;">
            <a href="/admin?password={ADMIN_PASSWORD}" style="color: var(--accent); text-decoration: none;">
                <i class="fas fa-cog"></i> Админ
            </a>
            {'<span style="color: var(--blue);"><i class="fas fa-check-circle"></i> ' + (user.get('da_username', 'DA') if user else 'DA') + '</span>' if (user and user['da_access_token']) else ''}
        </div>
        
        <div class="logo"><i class="fas fa-brain"></i></div>
        <h1 class="title">Mateus AI</h1>
        <p>Интеллектуальный помощник с системой токенов</p>
        
        <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: center; gap: 20px; align-items: center; flex-wrap: wrap;">
                <div style="background: rgba(50,205,50,0.15); color: var(--accent); padding: 12px 24px; border-radius: 20px;">
                    <i class="fas fa-{'rocket' if can_request else 'hourglass-end'}"></i>
                    <strong> {used}/{limit} запросов</strong> | Осталось: {remaining}
                </div>
                
                <div style="background: rgba(255, 169, 77, 0.15); color: var(--orange); padding: 12px 24px; border-radius: 20px;">
                    <i class="fas fa-coins"></i>
                    <strong> {tokens} токенов</strong>
                </div>
                
                {'<span class="badge badge-pro"><i class="fas fa-crown"></i> PRO</span>' if is_pro else '<span class="badge badge-free">FREE</span>'}
            </div>
        </div>
        
        {'' if (user and user['da_access_token']) else f'''
        <div style="margin-top: 20px;">
            <a href="/auth/donationalerts" class="btn btn-purple">
                <i class="fas fa-donate"></i> Подключить DonationAlerts для покупки токенов
            </a>
        </div>
        '''}
        
        {f'''
        <div style="margin-top: 15px;">
            <button onclick="checkDonations()" class="btn" style="background: rgba(151,117,250,0.2); border: 1px solid var(--purple);">
                <i class="fas fa-sync-alt"></i> Проверить новые донаты
            </button>
        </div>
        ''' if (user and user['da_access_token']) else ''}
        
        {f'''
        <div style="margin-top: 15px; color: var(--light); font-size: 0.9rem;">
            <i class="fas fa-bolt"></i> +{bonus_tokens} токенов за время в чате!
        </div>
        ''' if bonus_tokens > 0 else ''}
    </div>
    '''
    
    sidebar = f'''
    <div class="card">
        <h3><i class="fas fa-mask"></i> Роли AI</h3>
        <p style="color: var(--muted); margin-bottom: 20px; font-size: 0.9rem;">Выберите роль для AI</p>
        
        <div style="margin: 20px 0;">
            <button class="btn" onclick="selectRole('assistant')" style="width: 100%; margin-bottom: 10px; text-align: left;">
                <i class="fas fa-robot"></i> Помощник
            </button>
            <button class="btn" onclick="selectRole('programmer')" style="width: 100%; margin-bottom: 10px; text-align: left;">
                <i class="fas fa-code"></i> Программист
            </button>
            <button class="btn" onclick="selectRole('teacher')" style="width: 100%; margin-bottom: 10px; text-align: left;">
                <i class="fas fa-graduation-cap"></i> Учитель
            </button>
        </div>
        
        <div class="stat-card">
            <h4><i class="fas fa-chart-bar"></i> Статистика</h4>
            <div>Токены: <strong class="token-display">{tokens} <i class="fas fa-coins"></i></strong></div>
            <div>Запросы: <strong>{used}/{limit}</strong></div>
            <div>Статус: <strong>{'PRO ⭐' if is_pro else 'Free'}</strong></div>
            <div>Бонус: <strong>+{TOKENS_PER_HALF_HOUR} токенов/30 мин</strong></div>
        </div>
        
        <div style="background: rgba(255, 215, 0, 0.1); padding: 25px; border-radius: 15px; border: 1px solid var(--gold); margin-top: 20px;">
            <h4><i class="fas fa-crown"></i> PRO Подписка</h4>
            <p style="color: var(--muted); margin: 10px 0;">{PRO_PRICE_TOKENS} токенов на 30 дней</p>
            
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 2rem; color: gold; font-weight: bold;">{PRO_PRICE_TOKENS}</div>
                <div style="color: var(--muted); font-size: 0.9rem;">токенов</div>
            </div>
            
            <button class="btn btn-gold" onclick="buyProWithTokens()" style="width: 100%;">
                <i class="fas fa-bolt"></i> Купить PRO за токены
            </button>
            
            <p style="text-align: center; margin-top: 15px; font-size: 0.9rem;">
                <i class="fas fa-info-circle"></i> Лимит {PRO_LIMIT} запросов/день
            </p>
        </div>
        
        <div style="margin-top: 20px; text-align: center;">
            <a href="/shop" class="btn btn-purple" style="width: 100%;">
                <i class="fas fa-shopping-cart"></i> Магазин токенов
            </a>
        </div>
    </div>
    '''
    
    content = f'''
    <div class="card">
        <h3><i class="fas fa-comments"></i> Чат с Mateus AI</h3>
        <p style="color: var(--muted); margin-bottom: 20px;">
            Общайтесь и зарабатывайте токены! +{TOKENS_PER_HALF_HOUR} токенов каждые 30 минут
        </p>
        
        <div id="chatMessages" class="chat-messages">
            <div class="ai-message">
                <div style="font-weight: bold; margin-bottom: 8px;">
                    <i class="fas fa-robot"></i> Mateus AI
                </div>
                <div style="margin-top: 10px;">
                    <p>👋 <strong>Привет! Я ваш AI помощник Mateus с системой токенов.</strong></p>
                    
                    <div style="background: rgba(255, 169, 77, 0.1); padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid var(--orange);">
                        <p><i class="fas fa-coins" style="color: var(--orange);"></i> <strong>Система токенов:</strong></p>
                        <ul style="margin: 10px 0 10px 20px;">
                            <li>+{TOKENS_PER_HALF_HOUR} токенов за каждые 30 минут в чате</li>
                            <li>1 токен = 1 рубль при покупке</li>
                            <li>PRO подписка = {PRO_PRICE_TOKENS} токенов</li>
                            <li>Купить токены: Telegram {TELEGRAM_SUPPORT}</li>
                        </ul>
                    </div>
                    
                    <p><strong>Как купить токены:</strong></p>
                    <ol style="margin: 10px 0 10px 20px;">
                        <li>Подключите DonationAlerts (кнопка сверху)</li>
                        <li>Напишите мне в Telegram: {TELEGRAM_SUPPORT}</li>
                        <li>Я вышлю реквизиты для доната</li>
                        <li>Сделайте донат на нужную сумму (1 рубль = 1 токен)</li>
                        <li>Токены начислятся автоматически!</li>
                    </ol>
                    
                    <p style="margin-top: 15px; padding: 10px; background: rgba(50,205,50,0.1); border-radius: 8px;">
                        <i class="fas fa-lightbulb"></i> <strong>Просто общайтесь со мной и зарабатывайте токены!</strong>
                    </p>
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Введите ваш вопрос... (Enter для отправки)" autofocus>
            <button class="btn" onclick="sendMessage()" style="background: linear-gradient(135deg, var(--accent), #2a8c2a);">
                <i class="fas fa-paper-plane"></i> Отправить
            </button>
        </div>
    </div>
    
    <div class="card">
        <h3><i class="fas fa-history"></i> Последние транзакции</h3>
        <div style="max-height: 200px; overflow-y: auto; margin-top: 15px;">
            {"".join([f'''
            <div style="padding: 12px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between;">
                <div>
                    <i class="fas fa-{'arrow-up' if trans['type'] in ['earn', 'bonus', 'reward', 'purchase'] else 'arrow-down'}" 
                       style="color: {'var(--accent)' if trans['type'] in ['earn', 'bonus', 'reward', 'purchase'] else 'var(--red)'}"></i>
                    {trans['description']}
                </div>
                <div style="font-weight: bold; color: {'var(--accent)' if trans['type'] in ['earn', 'bonus', 'reward', 'purchase'] else 'var(--red)'}">
                    {('+' if trans['type'] in ['earn', 'bonus', 'reward', 'purchase'] else '-') + str(trans['amount'])}
                </div>
            </div>
            ''' for trans in recent_transactions]) if recent_transactions else '<p style="text-align: center; color: var(--muted); padding: 20px;">Нет транзакций</p>'}
        </div>
    </div>
    '''
    
    footer = f'''
    <div class="footer">
        <p>© {datetime.now().year} Mateus AI | Система токенов и монетизации</p>
        <p style="margin-top: 10px; font-size: 0.8rem; opacity: 0.8;">
            Поддержка: Telegram {TELEGRAM_SUPPORT} | 1 токен = 1 рубль | PRO: {PRO_PRICE_TOKENS} токенов
        </p>
        <p style="margin-top: 5px; font-size: 0.8rem; opacity: 0.6;">
            DonationAlerts OAuth: {"✅ Подключен" if (user and user['da_access_token']) else "❌ Не подключен"}
        </p>
    </div>
    '''
    
    return render_page('Mateus AI | Токены', header, sidebar, content, footer)

@app.route('/shop')
def shop():
    user_id = get_user_id()
    user = get_user_data(user_id)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM shop_items WHERE is_active = 1 ORDER BY token_price')
    shop_items = cursor.fetchall()
    conn.close()
    
    tokens = user['tokens'] if user else 0
    
    header = f'''
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="color: var(--accent); font-size: 2.5rem;">
            <i class="fas fa-shopping-cart"></i> Магазин токенов
        </h1>
        <p style="color: var(--muted);">Покупайте товары за токены</p>
        
        <div style="display: inline-block; background: rgba(255, 169, 77, 0.2); padding: 15px 30px; border-radius: 15px; margin-top: 20px; border: 2px solid var(--orange);">
            <div style="font-size: 1.2rem; color: var(--muted);">Ваш баланс:</div>
            <div class="token-display" style="font-size: 2.5rem; margin: 10px 0;">{tokens} <i class="fas fa-coins"></i></div>
        </div>
        
        <div style="margin-top: 20px;">
            <a href="/" class="btn">
                <i class="fas fa-arrow-left"></i> На главную
            </a>
            {'<a href="/auth/donationalerts" class="btn btn-purple" style="margin-left: 10px;"><i class="fas fa-donate"></i> Купить токены</a>' if not (user and user['da_access_token']) else ''}
        </div>
    </div>
    '''
    
    content = f'''
    <div class="card">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
    '''
    
    for item in shop_items:
        can_afford = tokens >= item['token_price']
        
        content += f'''
            <div class="shop-item">
                <h3 style="color: var(--accent); margin-bottom: 10px;">{item['name']}</h3>
                <p style="color: var(--muted); margin-bottom: 15px; min-height: 40px;">{item['description']}</p>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--orange);">
                        {item['token_price']} <i class="fas fa-coins"></i>
                    </div>
                    <div style="color: var(--muted); font-size: 0.9rem;">
                        {tokens}/{item['token_price']} токенов
                    </div>
                </div>
                
                <button onclick="buyShopItem('{item['id']}', '{item['name']}', {item['token_price']})" 
                        class="btn {'btn-gold' if can_afford else ''}" 
                        style="width: 100%;" 
                        {'disabled' if not can_afford else ''}>
                    <i class="fas fa-shopping-bag"></i> {'Купить' if can_afford else 'Недостаточно токенов'}
                </button>
            </div>
        '''
    
    content += '''
        </div>
    </div>
    
    <div class="card" style="margin-top: 30px;">
        <h3><i class="fas fa-info-circle"></i> Как купить токены?</h3>
        <div style="background: rgba(151,117,250,0.1); padding: 20px; border-radius: 10px; margin-top: 15px;">
            <ol style="margin: 10px 0 10px 20px; color: var(--text);">
                <li style="margin-bottom: 10px;">Подключите DonationAlerts (кнопка "Купить токены")</li>
                <li style="margin-bottom: 10px;">Напишите в Telegram поддержке: <strong>''' + TELEGRAM_SUPPORT + '''</strong></li>
                <li style="margin-bottom: 10px;">Я вышлю вам реквизиты для доната</li>
                <li style="margin-bottom: 10px;">Сделайте донат на нужную сумму (1 рубль = 1 токен)</li>
                <li style="margin-bottom: 10px;">Токены начислятся автоматически в течение 5 минут</li>
                <li>Покупайте товары в магазине за токены!</li>
            </ol>
            
            <div style="margin-top: 20px; padding: 15px; background: rgba(50,205,50,0.1); border-radius: 8px;">
                <p style="color: var(--accent); margin: 0;">
                    <i class="fas fa-bolt"></i> <strong>PRO подписка:</strong> {PRO_PRICE_TOKENS} токенов = {PRO_PRICE_TOKENS} рублей
                </p>
            </div>
        </div>
    </div>
    '''
    
    return render_page('Магазин токенов', header, '', content, '')

@app.route('/set_role', methods=['POST'])
def set_role():
    session['role'] = request.get_json().get('role', 'assistant')
    return jsonify({'success': True, 'role': session['role']})

@app.route('/check_time_bonus')
def check_time_bonus_route():
    user_id = get_user_id()
    bonus_tokens = check_and_award_tokens(user_id)
    
    if bonus_tokens > 0:
        user = get_user_data(user_id)
        return jsonify({
            'success': True,
            'bonus': bonus_tokens,
            'new_balance': user['tokens'] if user else 0
        })
    
    return jsonify({'success': False, 'bonus': 0})

@app.route('/check_donations')
def check_donations_route():
    user_id = get_user_id()
    new_donations = check_donationalerts_donations(user_id)
    
    if new_donations:
        user = get_user_data(user_id)
        return jsonify({
            'success': True,
            'new_donations': len(new_donations),
            'new_balance': user['tokens'] if user else 0
        })
    
    return jsonify({'success': False, 'new_donations': 0})

@app.route('/buy_pro_with_tokens', methods=['POST'])
def buy_pro_with_tokens():
    user_id = get_user_id()
    success, message = activate_pro_with_tokens(user_id)
    
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/buy_shop_item', methods=['POST'])
def buy_shop_item():
    user_id = get_user_id()
    data = request.get_json()
    item_id = data.get('item_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Получаем товар
    cursor.execute('SELECT * FROM shop_items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({'success': False, 'message': 'Товар не найден'})
    
    # Получаем пользователя
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    if user['tokens'] < item['token_price']:
        conn.close()
        return jsonify({'success': False, 'message': f'Недостаточно токенов. Нужно: {item["token_price"]}'})
    
    # Списание токенов
    new_balance = user['tokens'] - item['token_price']
    
    cursor.execute('''
        UPDATE users 
        SET tokens = ?, total_tokens_spent = total_tokens_spent + ?
        WHERE id = ?
    ''', (new_balance, item['token_price'], user_id))
    
    # Записываем транзакцию
    transaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO token_transactions (id, user_id, type, amount, description, balance_after, created_at)
        VALUES (?, ?, 'spend', ?, ?, ?, ?)
    ''', (transaction_id, user_id, item['token_price'], f'Покупка: {item["name"]}', new_balance, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # Если купили PRO
    reload_needed = False
    if item_id == 'pro_1month':
        success, pro_message = activate_pro_with_tokens(user_id)
        if success:
            return jsonify({
                'success': True,
                'message': pro_message,
                'new_balance': new_balance,
                'reload': True
            })
    
    return jsonify({
        'success': True,
        'message': f'Вы успешно купили "{item["name"]}"!',
        'new_balance': new_balance,
        'reload': reload_needed
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = get_user_id()
        
        # Начинаем отсчет времени если еще не начали
        check_and_award_tokens(user_id)
        
        can_request, limit, used, remaining = check_request_limit(user_id)
        if not can_request:
            return jsonify({
                'success': False,
                'error': f'🚫 Лимит запросов исчерпан ({used}/{limit}). '
                        f'Купите PRO подписку за {PRO_PRICE_TOKENS} токенов или подождите до завтра!'
            })
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Сообщение не может быть пустым'})
        
        if len(message) > 2000:
            return jsonify({'success': False, 'error': 'Сообщение слишком длинное (макс. 2000 символов)'})
        
        # Получаем роль
        role = session.get('role', 'assistant')
        
        # Получаем ответ от AI
        ai_response = get_ai_response(message, role)
        
        # Обновляем счетчик запросов
        update_user_requests(user_id)
        
        # Получаем обновленные данные пользователя
        user = get_user_data(user_id)
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'stats': {
                'tokens': user['tokens'] if user else 0,
                'is_pro': user['is_pro'] if user else False,
                'usage': {
                    'used': used + 1,
                    'limit': limit,
                    'remaining': remaining - 1
                }
            }
        })
        
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'})

@app.route('/add_tokens_manual', methods=['POST'])
def add_tokens_manual():
    """Админский метод для добавления токенов"""
    password = request.form.get('password')
    if password != ADMIN_PASSWORD:
        return "Ошибка доступа", 403
    
    user_id = request.form.get('user_id')
    amount = int(request.form.get('amount', 0))
    description = request.form.get('description', 'Ручное начисление')
    
    if not user_id or amount <= 0:
        return "Неверные параметры", 400
    
    success, new_balance = add_tokens(user_id, amount, description, 'bonus')
    
    return f'''
    <script>
        alert("✅ Начислено {amount} токенов пользователю {user_id}\\nНовый баланс: {new_balance}");
        location.href = "/admin?password={ADMIN_PASSWORD}";
    </script>
    '''

@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != ADMIN_PASSWORD:
        return '''
        <div style="max-width: 400px; margin: 100px auto; padding: 40px; background: var(--card); border-radius: 20px; text-align: center; border: 2px solid var(--accent);">
            <h2 style="color: var(--accent); margin-bottom: 30px;">
                <i class="fas fa-lock"></i> Админ-панель
            </h2>
            <form method="GET">
                <input type="password" name="password" placeholder="Введите пароль" 
                       style="width: 100%; padding: 15px; margin: 20px 0; border-radius: 10px; border: 1px solid var(--border); background: rgba(0,0,0,0.3); color: white; font-size: 1rem;">
                <button type="submit" 
                        style="width: 100%; padding: 15px; background: var(--accent); border: none; border-radius: 10px; color: white; font-size: 1rem; font-weight: bold; cursor: pointer; transition: all 0.3s;">
                    <i class="fas fa-sign-in-alt"></i> Войти
                </button>
            </form>
        </div>
        '''
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Статистика
    cursor.execute('SELECT COUNT(*) as count FROM users')
    users_total = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_pro = 1')
    pro_users = cursor.fetchone()['count']
    
    cursor.execute('SELECT SUM(requests_today) as total FROM users')
    requests_today = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT SUM(tokens) as total FROM users')
    total_tokens = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT SUM(amount) as total FROM token_transactions WHERE type = "purchase"')
    tokens_purchased = cursor.fetchone()['total'] or 0
    
    # Последние пользователи
    cursor.execute('''
        SELECT id, tokens, is_pro, requests_today, da_username, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 20
    ''')
    recent_users = cursor.fetchall()
    
    # Последние транзакции
    cursor.execute('''
        SELECT tt.*, u.da_username 
        FROM token_transactions tt
        LEFT JOIN users u ON tt.user_id = u.id
        ORDER BY tt.created_at DESC 
        LIMIT 20
    ''')
    recent_transactions = cursor.fetchall()
    
    conn.close()
    
    html = f'''
    <div style="max-width: 1400px; margin: 0 auto; padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
            <h1 style="color: var(--accent);">
                <i class="fas fa-cogs"></i> Админ-панель Mateus AI
            </h1>
            <div>
                <a href="/" class="btn">
                    <i class="fas fa-arrow-left"></i> На главную
                </a>
                <a href="/admin?password={ADMIN_PASSWORD}&refresh=1" class="btn" style="margin-left: 10px;">
                    <i class="fas fa-sync-alt"></i> Обновить
                </a>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0;">
            <div class="card" style="text-align: center;">
                <h3><i class="fas fa-users"></i> Пользователей</h3>
                <p style="font-size: 2.5rem; font-weight: bold; color: var(--accent);">{users_total}</p>
            </div>
            <div class="card" style="text-align: center;">
                <h3><i class="fas fa-crown"></i> PRO</h3>
                <p style="font-size: 2.5rem; font-weight: bold; color: gold;">{pro_users}</p>
            </div>
            <div class="card" style="text-align: center;">
                <h3><i class="fas fa-comments"></i> Запросы сегодня</h3>
                <p style="font-size: 2.5rem; font-weight: bold; color: var(--blue);">{requests_today}</p>
            </div>
            <div class="card" style="text-align: center;">
                <h3><i class="fas fa-coins"></i> Всего токенов</h3>
                <p style="font-size: 2.5rem; font-weight: bold; color: var(--orange);">{total_tokens}</p>
            </div>
            <div class="card" style="text-align: center;">
                <h3><i class="fas fa-money-bill-wave"></i> Куплено токенов</h3>
                <p style="font-size: 2.5rem; font-weight: bold; color: var(--purple);">{tokens_purchased}</p>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-plus-circle"></i> Начислить токены вручную</h2>
            <form method="POST" action="/add_tokens_manual" style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr; gap: 10px; align-items: end; margin-top: 20px;">
                <input type="hidden" name="password" value="{ADMIN_PASSWORD}">
                <div>
                    <label style="display: block; margin-bottom: 5px; color: var(--muted);">ID пользователя</label>
                    <input type="text" name="user_id" placeholder="user_id" required
                           style="width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border); background: rgba(0,0,0,0.3); color: white;">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; color: var(--muted);">Количество</label>
                    <input type="number" name="amount" placeholder="100" required min="1"
                           style="width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border); background: rgba(0,0,0,0.3); color: white;">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px; color: var(--muted);">Описание</label>
                    <input type="text" name="description" placeholder="Награда за активность" required
                           style="width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border); background: rgba(0,0,0,0.3); color: white;">
                </div>
                <button type="submit" class="btn" style="background: var(--accent); height: fit-content;">
                    <i class="fas fa-plus"></i> Начислить
                </button>
            </form>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-history"></i> Последние транзакции</h2>
            <div style="overflow-x: auto; margin-top: 20px;">
                <table style="width: 100%; border-collapse: collapse; background: rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden;">
                    <thead style="background: var(--primary);">
                        <tr>
                            <th style="padding: 15px; text-align: left;">Время</th>
                            <th style="padding: 15px; text-align: left;">Пользователь</th>
                            <th style="padding: 15px; text-align: left;">Тип</th>
                            <th style="padding: 15px; text-align: left;">Сумма</th>
                            <th style="padding: 15px; text-align: left;">Описание</th>
                            <th style="padding: 15px; text-align: left;">Баланс после</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    for trans in recent_transactions:
        trans_time = datetime.fromisoformat(trans['created_at']).strftime('%H:%M %d.%m')
        amount_color = 'var(--accent)' if trans['type'] in ['earn', 'bonus', 'reward', 'purchase'] else 'var(--red)'
        amount_sign = '+' if trans['type'] in ['earn', 'bonus', 'reward', 'purchase'] else '-'
        
        html += f'''
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 12px;">{trans_time}</td>
                            <td style="padding: 12px;">{trans['da_username'] or trans['user_id'][:8]}...</td>
                            <td style="padding: 12px;">{trans['type']}</td>
                            <td style="padding: 12px; color: {amount_color}; font-weight: bold;">{amount_sign}{trans['amount']}</td>
                            <td style="padding: 12px;">{trans['description'][:50]}{'...' if len(trans['description']) > 50 else ''}</td>
                            <td style="padding: 12px; font-weight: bold;">{trans['balance_after']}</td>
                        </tr>
        '''
    
    html += '''
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-user-clock"></i> Последние пользователи</h2>
            <div style="overflow-x: auto; margin-top: 20px;">
                <table style="width: 100%; border-collapse: collapse; background: rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden;">
                    <thead style="background: var(--primary);">
                        <tr>
                            <th style="padding: 15px; text-align: left;">ID</th>
                            <th style="padding: 15px; text-align: left;">DA</th>
                            <th style="padding: 15px; text-align: left;">Токены</th>
                            <th style="padding: 15px; text-align: left;">PRO</th>
                            <th style="padding: 15px; text-align: left;">Запросы</th>
                            <th style="padding: 15px; text-align: left;">Создан</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    for user in recent_users:
        user_time = datetime.fromisoformat(user['created_at']).strftime('%d.%m %H:%M') if user['created_at'] else '-'
        
        html += f'''
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 12px;"><code>{user['id'][:8]}...</code></td>
                            <td style="padding: 12px;">{user['da_username'] or '-'}</td>
                            <td style="padding: 12px; font-weight: bold; color: var(--orange);">{user['tokens'] or 0}</td>
                            <td style="padding: 12px;">{"✅" if user['is_pro'] else "❌"}</td>
                            <td style="padding: 12px;">{user['requests_today'] or 0}</td>
                            <td style="padding: 12px;">{user_time}</td>
                        </tr>
        '''
    
    html += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return html

@app.route('/health')
def health():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(tokens) FROM users')
    total_tokens = cursor.fetchone()[0] or 0
    conn.close()
    
    return jsonify({
        'status': 'healthy',
        'service': 'Mateus AI',
        'timestamp': datetime.now().isoformat(),
        'users': users_count,
        'total_tokens': total_tokens,
        'openai_configured': bool(OPENAI_API_KEY),
        'donationalerts_configured': bool(DONATIONALERTS_CLIENT_ID),
        'token_system': 'active',
        'version': '3.0'
    })

# ==================== ЗАПУСК СЕРВЕРА ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Запуск Mateus AI v3.0 на порту {port}")
    print(f"📊 База данных: data.db")
    print(f"🪙 Система токенов: активна")
    print(f"   • +{TOKENS_PER_HALF_HOUR} токенов/30 мин в чате")
    print(f"   • PRO подписка: {PRO_PRICE_TOKENS} токенов")
    print(f"🤖 OpenAI: {'✅ Настроен' if OPENAI_API_KEY else '❌ Не настроен'}")
    print(f"💰 DonationAlerts OAuth: {'✅ Настроен' if DONATIONALERTS_CLIENT_ID else '❌ Не настроен'}")
    print(f"📞 Поддержка: Telegram {TELEGRAM_SUPPORT}")
    app.run(host='0.0.0.0', port=port, debug=False)
