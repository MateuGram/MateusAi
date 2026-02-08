import os
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, render_template_string
import urllib.parse
import re
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mateus-ai-super-secret-2024')
app.permanent_session_lifetime = timedelta(days=30)

# База данных в памяти
users_db = {}
admin_password = os.environ.get('ADMIN_PASSWORD', 'MateusAdmin2024!')

# Настройки
MAX_FREE_REQUESTS = 34
TOKENS_FOR_PRO = 1000
TOKENS_PER_REQUEST = 10

class WebSearcher:
    """Класс для поиска информации в интернете"""
    
    @staticmethod
    def search_duckduckgo(query, num_results=5):
        """Поиск через DuckDuckGo HTML"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://duckduckgo.com/',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Парсим результаты
            results = []
            html = response.text
            
            # Ищем ссылки на результаты
            links = re.findall(r'<a class="result__url" href="([^"]+)"', html)
            titles = re.findall(r'<a class="result__snippet" href="[^"]+">([^<]+)</a>', html)
            
            for i, (link, title) in enumerate(zip(links[:num_results], titles[:num_results])):
                if link.startswith('//'):
                    link = 'https:' + link
                
                results.append({
                    'title': title.strip(),
                    'link': link,
                    'source': 'DuckDuckGo'
                })
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска DuckDuckGo: {e}")
            return []
    
    @staticmethod
    def search_google(query, num_results=3):
        """Альтернативный поиск через Google (использует API)"""
        try:
            # Используем Google Custom Search API если есть ключ
            api_key = os.environ.get('GOOGLE_API_KEY', '')
            search_engine_id = os.environ.get('GOOGLE_SEARCH_ID', '')
            
            if api_key and search_engine_id:
                url = f"https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': api_key,
                    'cx': search_engine_id,
                    'q': query,
                    'num': num_results
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'source': 'Google'
                        })
                    
                    return results
            
            # Если нет API, используем HTML парсинг
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            html = response.text
            
            # Простой парсинг Google результатов
            results = []
            pattern = r'<div class="[^"]*"><a href="([^"]+)"[^>]*><h3[^>]*>([^<]+)</h3></a>'
            
            matches = re.findall(pattern, html)
            for match in matches[:num_results]:
                link, title = match
                if link.startswith('/url?q='):
                    link = link[7:].split('&')[0]
                
                results.append({
                    'title': title,
                    'link': urllib.parse.unquote(link),
                    'source': 'Google'
                })
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска Google: {e}")
            return []
    
    @staticmethod
    def search_wikipedia(query):
        """Поиск в Википедии"""
        try:
            url = f"https://ru.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'utf8': 1,
                'srlimit': 3
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('query', {}).get('search', []):
                    page_id = item.get('pageid')
                    title = item.get('title', '')
                    snippet = item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', '')
                    
                    if page_id:
                        page_url = f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                        
                        results.append({
                            'title': title,
                            'link': page_url,
                            'snippet': snippet,
                            'source': 'Wikipedia'
                        })
                
                return results
                
        except Exception as e:
            print(f"Ошибка поиска Wikipedia: {e}")
            return []
    
    @staticmethod
    def get_page_content(url):
        """Получение содержимого веб-страницы"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return ""
            
            # Извлекаем текст
            text = response.text
            
            # Удаляем HTML теги
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # Убираем лишние пробелы
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:2000]  # Ограничиваем длину
            
        except Exception as e:
            print(f"Ошибка получения контента: {e}")
            return ""
    
    @staticmethod
    def get_current_time():
        """Получение текущего времени"""
        try:
            # Пробуем получить время из интернета
            response = requests.get('http://worldtimeapi.org/api/timezone/Europe/Moscow', timeout=3)
            if response.status_code == 200:
                data = response.json()
                return data.get('datetime', '')
        except:
            pass
        
        # Если не получилось, используем локальное время
        return datetime.now().isoformat()
    
    @staticmethod
    def search_comprehensive(query):
        """Комплексный поиск по всем источникам"""
        all_results = []
        
        # Ищем в DuckDuckGo
        ddg_results = WebSearcher.search_duckduckgo(query, 3)
        all_results.extend(ddg_results)
        
        # Ищем в Wikipedia (особенно для фактов)
        wiki_results = WebSearcher.search_wikipedia(query)
        all_results.extend(wiki_results)
        
        # Если мало результатов, пробуем Google
        if len(all_results) < 3:
            google_results = WebSearcher.search_google(query, 2)
            all_results.extend(google_results)
        
        # Убираем дубликаты
        unique_results = []
        seen_links = set()
        
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
        
        return unique_results[:5]

class MateusAI:
    def __init__(self):
        self.searcher = WebSearcher()
        self.conversation_history = {}
        
    def process_query(self, query, username):
        """Основная обработка запроса"""
        query_lower = query.lower().strip()
        
        # Обновляем историю диалога
        if username not in self.conversation_history:
            self.conversation_history[username] = []
        
        # Добавляем запрос в историю
        self.conversation_history[username].append({
            'role': 'user',
            'content': query,
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничиваем историю
        if len(self.conversation_history[username]) > 10:
            self.conversation_history[username] = self.conversation_history[username][-10:]
        
        # Специальные команды
        if query_lower in ['время', 'дата', 'сейчас', 'time', 'date']:
            return self._handle_time_query()
        
        if query_lower in ['привет', 'hello', 'hi', 'здравствуй']:
            return self._handle_greeting(username)
        
        if query_lower in ['помощь', 'help', 'команды']:
            return self._handle_help()
        
        if query_lower in ['о себе', 'кто ты', 'что ты']:
            return self._handle_about()
        
        if query_lower in ['токены', 'баланс', 'статистика']:
            return self._handle_tokens_info()
        
        # Поиск информации в интернете
        search_results = self.searcher.search_comprehensive(query)
        
        if not search_results:
            return {
                'answer': f"🤖 **Mateus AI:**\n\nК сожалению, по запросу '{query}' не удалось найти информацию в открытых источниках.\n\n💡 **Советы:**\n1. Проверьте правильность написания\n2. Попробуйте переформулировать вопрос\n3. Используйте другие ключевые слова\n\n*Я продолжаю учиться и улучшать поиск!*",
                'sources': [],
                'confidence': 'низкая'
            }
        
        # Получаем дополнительную информацию из найденных страниц
        enriched_results = []
        for result in search_results[:3]:  # Ограничиваем количество
            try:
                content = self.searcher.get_page_content(result['link'])
                if content:
                    result['content'] = content[:500]  # Берем первые 500 символов
                    enriched_results.append(result)
            except:
                continue
        
        # Формируем ответ на основе найденной информации
        return self._generate_response(query, enriched_results)
    
    def _handle_time_query(self):
        """Обработка запроса времени"""
        time_str = self.searcher.get_current_time()
        
        try:
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                dt = datetime.now()
            
            weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            
            response = f"🕒 **Текущее время и дата:**\n\n"
            response += f"📅 **Дата:** {dt.strftime('%d.%m.%Y')}\n"
            response += f"📆 **День недели:** {weekdays[dt.weekday()]}\n"
            response += f"⏰ **Время:** {dt.strftime('%H:%M:%S')}\n"
            response += f"🌍 **Часовой пояс:** UTC+3 (Москва)\n\n"
            response += f"*Информация получена из интернета*"
            
            return {
                'answer': response,
                'sources': [],
                'confidence': 'высокая'
            }
            
        except:
            dt = datetime.now()
            response = f"🕒 **Текущее время:**\n\n"
            response += f"📅 **Дата:** {dt.strftime('%d.%m.%Y')}\n"
            response += f"⏰ **Время:** {dt.strftime('%H:%M:%S')}\n\n"
            response += f"*Локальное время сервера*"
            
            return {
                'answer': response,
                'sources': [],
                'confidence': 'средняя'
            }
    
    def _handle_greeting(self, username):
        """Приветствие"""
        greetings = [
            f"🤖 **Привет, {username}!** Я Mateus AI - нейросеть для поиска информации в интернете.",
            f"👋 **Здравствуйте, {username}!** Я готов помочь вам найти любую информацию.",
            f"🎯 **Добро пожаловать, {username}!** Задавайте вопросы, а я буду искать ответы в интернете."
        ]
        
        response = random.choice(greetings) + "\n\n"
        response += "🔍 **Что я умею:**\n"
        response += "• Искать информацию в интернете\n"
        response += "• Анализировать и сравнивать данные\n"
        response += "• Отвечать на вопросы с источниками\n"
        response += "• Показывать актуальное время\n\n"
        response += "💡 **Примеры запросов:**\n"
        response += "• 'Какая погода в Москве?'\n"
        response += "• 'Кто создал Python?'\n"
        response += "• 'Новости технологий сегодня'\n"
        response += "• 'Что такое блокчейн?'"
        
        return {
            'answer': response,
            'sources': [],
            'confidence': 'высокая'
        }
    
    def _handle_help(self):
        """Помощь"""
        response = "🤖 **Помощь по Mateus AI**\n\n"
        response += "📋 **Основные команды:**\n"
        response += "• 'время' или 'дата' - текущее время\n"
        response += "• 'помощь' - эта справка\n"
        response += "• 'о себе' - информация обо мне\n"
        response += "• 'токены' - ваш баланс токенов\n\n"
        response += "🔍 **Как работает поиск:**\n"
        response += "1. Вы задаете вопрос\n"
        response += "2. Я ищу информацию в интернете\n"
        response += "3. Анализирую найденные данные\n"
        response += "4. Предоставляю точный ответ с источниками\n\n"
        response += "💎 **Подписка Pro:**\n"
        response += f"• {TOKENS_FOR_PRO} токенов = Pro подписка\n"
        response += "• Неограниченные запросы\n"
        response += "• Приоритетная обработка\n\n"
        response += "🚀 **Просто задайте вопрос - и я найду ответ!**"
        
        return {
            'answer': response,
            'sources': [],
            'confidence': 'высокая'
        }
    
    def _handle_about(self):
        """Информация о себе"""
        response = "🤖 **Mateus AI** - умная нейросеть для поиска информации\n\n"
        response += "🎯 **Миссия:** Помогать людям находить точную информацию в интернете\n\n"
        response += "⚡ **Технологии:**\n"
        response += "• Поиск в DuckDuckGo, Google, Wikipedia\n"
        response += "• Анализ и сравнение данных\n"
        response += "• Обработка естественного языка\n"
        response += "• Работа в реальном времени\n\n"
        response += "📊 **Статистика:**\n"
        response += f"• Бесплатно: {MAX_FREE_REQUESTS} запросов/день\n"
        response += f"• Pro: неограниченно\n"
        response += f"• Токены: {TOKENS_PER_REQUEST} за запрос\n\n"
        response += "🌟 **Разработано для быстрого и точного поиска информации!**"
        
        return {
            'answer': response,
            'sources': [],
            'confidence': 'высокая'
        }
    
    def _handle_tokens_info(self):
        """Информация о токенах"""
        response = "💰 **Система токенов Mateus AI**\n\n"
        response += f"🎯 **Бесплатные пользователи:**\n"
        response += f"• {MAX_FREE_REQUESTS} запросов в день\n"
        response += f"• {TOKENS_PER_REQUEST} токенов за каждый запрос\n"
        response += f"• Накопление токенов для апгрейда\n\n"
        response += f"💎 **Подписка Pro ({TOKENS_FOR_PRO} токенов):**\n"
        response += "• Неограниченные запросы\n"
        response += "• Приоритетная обработка\n"
        response += "• Расширенный анализ\n"
        response += "• Экспериментальные функции\n\n"
        response += "📈 **Как получить токены:**\n"
        response += "1. Задавайте вопросы (10 токенов/запрос)\n"
        response += f"2. Накопите {TOKENS_FOR_PRO} токенов\n"
        response += "3. Активируйте Pro подписку\n\n"
        response += "🚀 **Чем больше вопросов - тем быстрее Pro!**"
        
        return {
            'answer': response,
            'sources': [],
            'confidence': 'высокая'
        }
    
    def _generate_response(self, query, search_results):
        """Генерация ответа на основе найденной информации"""
        if not search_results:
            return {
                'answer': f"🤖 **Mateus AI:**\n\nНе удалось найти информацию по запросу '{query}'.\n\nПопробуйте переформулировать вопрос.",
                'sources': [],
                'confidence': 'низкая'
            }
        
        # Анализируем результаты
        main_result = search_results[0]
        
        # Извлекаем ключевую информацию
        content = main_result.get('content', '')
        title = main_result.get('title', 'Результат поиска')
        
        # Формируем ответ
        response = f"🤖 **Mateus AI отвечает:**\n\n"
        response += f"🔍 **По вашему запросу '{query}' найдена информация:**\n\n"
        
        # Добавляем основную информацию
        if content:
            # Обрезаем и форматируем
            summary = content[:400]
            if len(content) > 400:
                summary += "..."
            response += f"📝 **{title}:** {summary}\n\n"
        else:
            response += f"📝 **{title}**\n\n"
        
        # Добавляем источники
        response += "📚 **Источники информации:**\n"
        for i, result in enumerate(search_results[:3], 1):
            source_name = result.get('source', 'Интернет')
            response += f"{i}. {result.get('title', 'Источник')} ({source_name})\n"
        
        # Добавляем рекомендации
        response += "\n💡 **Рекомендации:**\n"
        response += "• Информация взята из открытых источников\n"
        response += "• Для углубленного изучения посетите указанные сайты\n"
        
        # Определяем уверенность
        confidence = 'высокая' if len(search_results) >= 2 else 'средняя'
        
        return {
            'answer': response,
            'sources': [r.get('link', '') for r in search_results[:3]],
            'confidence': confidence
        }

# Инициализация ИИ
ai = MateusAI()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_data(username):
    if username not in users_db:
        today = datetime.now().strftime('%Y-%m-%d')
        users_db[username] = {
            'password': None,
            'tokens': 100,
            'subscription': 'free',
            'daily_requests': 0,
            'last_date': today,
            'created': datetime.now().isoformat()
        }
    return users_db[username]

# HTML интерфейс (сохраняем из предыдущей версии, но упрощаем)
HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mateus AI - Умная нейросеть</title>
    <style>
        :root {
            --neon: #00ff88;
            --dark: #0a0a0a;
            --card: #111;
            --text: #fff;
            --gray: #888;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: var(--dark); color: var(--text); font-family: Arial, sans-serif; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { text-align: center; padding: 30px 0; }
        .logo { font-size: 48px; font-weight: bold; color: var(--neon); text-shadow: 0 0 10px var(--neon); margin-bottom: 10px; }
        .slogan { color: var(--gray); margin-bottom: 20px; }
        .main { display: flex; gap: 30px; flex-wrap: wrap; }
        .chat { flex: 1; min-width: 300px; }
        .sidebar { width: 350px; min-width: 300px; }
        .card { background: var(--card); border: 1px solid #222; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
        .messages { height: 400px; overflow-y: auto; padding: 15px; background: #000; border-radius: 10px; margin-bottom: 20px; border: 1px solid #222; }
        .message { padding: 12px 15px; margin-bottom: 10px; border-radius: 10px; max-width: 85%; }
        .user-msg { background: linear-gradient(45deg, #003322, #005533); margin-left: auto; border: 1px solid var(--neon); }
        .ai-msg { background: #1a1a1a; margin-right: auto; border: 1px solid #333; white-space: pre-line; }
        .input-row { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 15px; background: #000; border: 2px solid var(--neon); border-radius: 10px; color: white; font-size: 16px; }
        .btn { padding: 15px 25px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; }
        .btn-primary { background: linear-gradient(45deg, #003322, var(--neon)); color: black; }
        .btn-premium { background: linear-gradient(45deg, #330066, #8800ff); color: white; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; }
        .modal-content { background: var(--card); max-width: 400px; margin: 100px auto; padding: 30px; border-radius: 15px; border: 2px solid var(--neon); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">MATEUS AI</div>
            <div class="slogan">Умная нейросеть для поиска информации</div>
            <div id="userPanel"></div>
        </header>
        <div class="main">
            <div class="chat">
                <div class="card">
                    <h3 style="color: var(--neon);">💬 Чат с Mateus AI</h3>
                    <div class="messages" id="chat">
                        <div class="message ai-msg">🤖 Привет! Я умная нейросеть для поиска информации. Задайте вопрос, и я найду ответ в интернете!</div>
                    </div>
                    <div class="input-row">
                        <input type="text" id="question" placeholder="Введите ваш вопрос..." autocomplete="off">
                        <button class="btn btn-primary" onclick="askAI()">Отправить</button>
                    </div>
                    <div id="loading" style="display:none; color:var(--neon);">🔍 Ищу информацию в интернете...</div>
                </div>
            </div>
            <div class="sidebar">
                <div class="card">
                    <h3 style="color: var(--neon);">📊 Статистика</h3>
                    <div id="stats">
                        <div style="margin: 15px 0;"><strong>Токены:</strong> <span id="tokens">0</span></div>
                        <div style="margin: 15px 0;"><strong>Подписка:</strong> <span id="sub">Free</span></div>
                        <div style="margin: 15px 0;"><strong>Запросы сегодня:</strong> <span id="requests">0/34</span></div>
                    </div>
                    <button class="btn btn-premium" onclick="upgrade()" style="width:100%;margin:10px 0;">💎 Апгрейд до Pro</button>
                    <button class="btn" onclick="admin()" style="width:100%;margin:10px 0;background:#333;color:white;">🔧 Админ-панель</button>
                    <button class="btn" onclick="logout()" style="width:100%;margin:10px 0;background:#660000;color:white;">🚪 Выйти</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Модалки -->
    <div class="modal" id="loginModal">
        <div class="modal-content">
            <h3 style="color:var(--neon);margin-bottom:20px;">🔐 Вход / Регистрация</h3>
            <input type="text" id="username" placeholder="Имя пользователя" style="width:100%;padding:12px;margin-bottom:10px;">
            <input type="password" id="password" placeholder="Пароль" style="width:100%;padding:12px;margin-bottom:10px;">
            <div id="loginError" style="color:#ff4444;margin-bottom:10px;"></div>
            <button class="btn btn-primary" onclick="login()" style="width:100%;">Войти / Создать аккаунт</button>
            <button onclick="closeModal('loginModal')" style="position:absolute;top:10px;right:15px;color:var(--neon);font-size:24px;background:none;border:none;cursor:pointer;">×</button>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        function showLoginModal() {
            document.getElementById('loginModal').style.display = 'block';
        }
        
        function closeModal(id) {
            document.getElementById(id).style.display = 'none';
        }
        
        async function login() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            
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
                addMessage('🤖 Добро пожаловать! Задавайте вопросы, я найду информацию в интернете.', 'ai');
            } else {
                document.getElementById('loginError').textContent = data.error;
            }
        }
        
        async function askAI() {
            if (!currentUser) {
                showLoginModal();
                return;
            }
            
            const question = document.getElementById('question').value.trim();
            if (!question) return;
            
            addMessage(question, 'user');
            document.getElementById('question').value = '';
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.answer, 'ai');
                    updateUI();
                } else {
                    addMessage('❌ ' + data.error, 'ai');
                }
            } catch (e) {
                addMessage('❌ Ошибка сети', 'ai');
            }
            
            document.getElementById('loading').style.display = 'none';
        }
        
        function addMessage(text, type) {
            const chat = document.getElementById('chat');
            const msg = document.createElement('div');
            msg.className = `message ${type}-msg`;
            msg.textContent = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function updateUI() {
            const userPanel = document.getElementById('userPanel');
            const tokens = document.getElementById('tokens');
            const sub = document.getElementById('sub');
            const requests = document.getElementById('requests');
            
            if (currentUser) {
                userPanel.innerHTML = `<div style="text-align:center;margin-bottom:10px;">👤 <strong>${currentUser.username}</strong> ${currentUser.subscription === 'pro' ? '💎' : ''}</div>`;
                tokens.textContent = currentUser.tokens;
                sub.textContent = currentUser.subscription;
                sub.style.color = currentUser.subscription === 'pro' ? '#8800ff' : 'var(--neon)';
                requests.textContent = `${currentUser.daily_requests}/34`;
            } else {
                userPanel.innerHTML = '<button class="btn btn-primary" onclick="showLoginModal()">Войти</button>';
                tokens.textContent = '0';
                sub.textContent = 'None';
                requests.textContent = '0/0';
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
            } catch (e) {}
        }
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', () => {
            checkAuth();
            setTimeout(() => {
                if (!currentUser) showLoginModal();
            }, 1000);
            
            // Enter для отправки
            document.getElementById('question').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') askAI();
            });
        });
        
        // Закрытие модалок
        window.onclick = (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
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
            return jsonify({'success': False, 'error': 'Имя минимум 3 символа'})
        
        user = get_user_data(username)
        password_hash = hash_password(password)
        
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
        response = ai.process_query(question, username)
        
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

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'users': len(users_db)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Mateus AI запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
