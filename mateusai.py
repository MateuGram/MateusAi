import os
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import re

app = Flask(__name__)
CORS(app)

# API ключ Ollama (бесплатный)
OLLAMA_API_KEY = "cabb2fcef2e249fcb03c5cb80a47fb89.xfcCSfYXoLYnyDdZWoIwyY38"
OLLAMA_URL = "https://api.ollama.ai/v1/completions"  # API endpoint

# Хранилище задач
tasks = {}

def fetch_web_content(url):
    """Получение контента с веб-страницы"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Ограничиваем размер
    except Exception as e:
        return f"Ошибка загрузки страницы: {str(e)}"

def search_web(query):
    """Поиск в интернете через Google Custom Search"""
    # Используем бесплатный поиск через Google (без API)
    try:
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for g in soup.find_all('div', class_='g')[:5]:  # Первые 5 результатов
            title = g.find('h3')
            link = g.find('a')
            if title and link:
                href = link.get('href', '')
                if 'url?q=' in href:
                    url = href.split('url?q=')[1].split('&')[0]
                    results.append({
                        'title': title.text,
                        'url': url
                    })
        return results
    except Exception as e:
        return [{'error': f'Ошибка поиска: {str(e)}'}]

def process_with_ollama(prompt, context=""):
    """Обработка запроса через Ollama"""
    try:
        headers = {
            'Authorization': f'Bearer {OLLAMA_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        full_prompt = f"Контекст из интернета:\n{context}\n\nЗапрос пользователя: {prompt}\n\nОтвет:"
        
        data = {
            "model": "llama2",  # или другая модель
            "prompt": full_prompt,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(OLLAMA_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('text', 'Нет ответа')
        else:
            # Если API не работает, используем локальную логику
            return process_locally(prompt, context)
            
    except Exception as e:
        return f"Ошибка AI: {str(e)}"

def process_locally(prompt, context=""):
    """Локальная обработка если API недоступен"""
    if "погода" in prompt.lower():
        return "Для получения погоды нужен доступ к API погоды. Попробуйте позже."
    elif "новости" in prompt.lower():
        return "Последние новости можно найти на новостных сайтах."
    else:
        return f"Получил запрос: {prompt}\nКонтекст: {context[:200]}..."

def execute_task(task_id, prompt):
    """Выполнение задачи с доступом в интернет"""
    try:
        tasks[task_id]['status'] = 'processing'
        
        # Шаг 1: Поиск в интернете
        search_results = search_web(prompt)
        
        # Шаг 2: Получение контента с найденных страниц
        web_context = f"Результаты поиска по запросу '{prompt}':\n"
        
        if search_results and not 'error' in search_results[0]:
            for i, result in enumerate(search_results[:3], 1):
                web_context += f"\n{i}. {result['title']}\nURL: {result['url']}\n"
                content = fetch_web_content(result['url'])
                web_context += f"Содержание: {content[:500]}...\n"
        
        # Шаг 3: Обработка через AI
        ai_response = process_with_ollama(prompt, web_context)
        
        # Шаг 4: Сохранение результата
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = {
            'prompt': prompt,
            'search_results': search_results,
            'web_context': web_context[:1000],
            'ai_response': ai_response,
            'timestamp': str(time.time())
        }
        
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['result'] = {'error': str(e)}

@app.route('/')
def home():
    return jsonify({
        'service': 'MateusAI',
        'status': 'active',
        'description': 'AI с доступом в интернет',
        'endpoints': {
            '/task': 'POST - Создать новую задачу',
            '/task/<task_id>': 'GET - Получить результат задачи',
            '/search': 'POST - Поиск в интернете',
            '/ask': 'POST - Задать вопрос AI'
        }
    })

@app.route('/task', methods=['POST'])
def create_task():
    """Создание новой задачи"""
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'Укажите prompt'}), 400
    
    task_id = str(time.time()).replace('.', '')
    tasks[task_id] = {
        'status': 'queued',
        'prompt': prompt,
        'created': time.time()
    }
    
    # Запускаем выполнение в фоне
    thread = threading.Thread(target=execute_task, args=(task_id, prompt))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'queued',
        'message': 'Задача создана, выполняется...'
    })

@app.route('/task/<task_id>', methods=['GET'])
def get_task(task_id):
    """Получение результата задачи"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Задача не найдена'}), 404
    
    return jsonify(task)

@app.route('/search', methods=['POST'])
def search():
    """Быстрый поиск в интернете"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Укажите query'}), 400
    
    results = search_web(query)
    return jsonify({'query': query, 'results': results})

@app.route('/ask', methods=['POST'])
def ask():
    """Быстрый вопрос к AI"""
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'Укажите question'}), 400
    
    # Поиск в интернете
    search_results = search_web(question)
    
    # Получаем контент с первой страницы
    web_context = ""
    if search_results and not 'error' in search_results[0]:
        first_result = search_results[0]
        web_context = fetch_web_content(first_result['url'])
    
    # Ответ AI
    answer = process_with_ollama(question, web_context)
    
    return jsonify({
        'question': question,
        'answer': answer,
        'sources': search_results[:3]
    })

@app.route('/admin/status', methods=['GET'])
def status():
    """Статус сервиса"""
    return jsonify({
        'active_tasks': len([t for t in tasks.values() if t['status'] == 'processing']),
        'total_tasks': len(tasks),
        'ollama_api': 'configured',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
