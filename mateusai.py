import os
import requests
import json
import time
import threading
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# API ключ Ollama
OLLAMA_API_KEY = "cabb2fcef2e249fcb03c5cb80a47fb89.xfcCSfYXoLYnyDdZWoIwyY38"
OLLAMA_URL = "https://api.ollama.ai/v1/completions"

# Хранилище истории чата
chat_history = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MateusAI - Чат с ИИ</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
            justify-content: flex-end;
        }
        
        .bot-message {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 20px;
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        
        .user-message .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message-time {
            font-size: 11px;
            margin-top: 5px;
            opacity: 0.7;
            text-align: right;
        }
        
        .typing-indicator {
            display: flex;
            padding: 12px 18px;
            background: white;
            border-radius: 20px;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            width: fit-content;
        }
        
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
            30% { transform: translateY(-10px); opacity: 1; }
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #eee;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input input:focus {
            border-color: #667eea;
        }
        
        .chat-input button {
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .chat-input button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .chat-input button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .sources {
            font-size: 12px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            color: #666;
        }
        
        .sources a {
            color: #667eea;
            text-decoration: none;
        }
        
        .sources a:hover {
            text-decoration: underline;
        }
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            background: #4caf50;
            color: white;
            border-radius: 12px;
            font-size: 11px;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>MateusAI <span class="status-badge">Online</span></h1>
            <p>ИИ с доступом в интернет • Задавай любые вопросы</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                <div class="message-content">
                    Привет! Я MateusAI - твой умный помощник с доступом в интернет. 
                    Могу искать информацию, отвечать на вопросы и выполнять задачи. 
                    Что хочешь узнать? 🌟
                    <div class="message-time">{{ current_time }}</div>
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()" id="sendButton">Отправить</button>
        </div>
    </div>

    <script>
        let isTyping = false;
        
        function addMessage(text, isUser, sources = null) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            let messageHTML = `
                <div class="message-content">
                    ${text}
                    <div class="message-time">${time}</div>
            `;
            
            if (sources) {
                messageHTML += `
                    <div class="sources">
                        <strong>Источники:</strong><br>
                        ${sources}
                    </div>
                `;
            }
            
            messageHTML += `</div>`;
            messageDiv.innerHTML = messageHTML;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function showTypingIndicator() {
            if (isTyping) return;
            isTyping = true;
            
            const messagesDiv = document.getElementById('chatMessages');
            const indicator = document.createElement('div');
            indicator.className = 'message bot-message';
            indicator.id = 'typingIndicator';
            indicator.innerHTML = `
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messagesDiv.appendChild(indicator);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function removeTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) {
                indicator.remove();
            }
            isTyping = false;
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message || isTyping) return;
            
            // Добавляем сообщение пользователя
            addMessage(message, true);
            input.value = '';
            
            // Показываем индикатор печати
            showTypingIndicator();
            
            try {
                // Отправляем запрос к нашему API
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ question: message })
                });
                
                const data = await response.json();
                
                // Убираем индикатор печати
                removeTypingIndicator();
                
                // Форматируем источники
                let sourcesHTML = '';
                if (data.sources && data.sources.length > 0) {
                    sourcesHTML = data.sources.map(s => 
                        `<a href="${s.url}" target="_blank">${s.title}</a>`
                    ).join('<br>');
                }
                
                // Добавляем ответ бота
                addMessage(data.answer, false, sourcesHTML);
                
            } catch (error) {
                removeTypingIndicator();
                addMessage('Извини, произошла ошибка. Попробуй еще раз.', false);
                console.error('Error:', error);
            }
        }
        
        // Обработка Enter
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
'''

def fetch_web_content(url):
    """Получение контента с веб-страницы"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:3000]
    except:
        return ""

def search_web(query):
    """Поиск в интернете"""
    try:
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for g in soup.find_all('div', class_='g')[:3]:
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
    except:
        return []

def process_with_ollama(prompt, context=""):
    """Обработка через Ollama"""
    try:
        headers = {
            'Authorization': f'Bearer {OLLAMA_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        full_prompt = f"Контекст из интернета:\n{context}\n\nВопрос: {prompt}\n\nОтвет (на русском, подробно):"
        
        data = {
            "model": "llama2",
            "prompt": full_prompt,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(OLLAMA_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('text', 'Нет ответа')
        else:
            return f"Вот что я нашел по запросу '{prompt}'. (Использую локальный режим)"
            
    except:
        return f"Ищу информацию по вашему вопросу: '{prompt}'..."

@app.route('/')
def home():
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M")
    return render_template_string(HTML_TEMPLATE, current_time=current_time)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'Укажите вопрос'}), 400
    
    # Поиск в интернете
    search_results = search_web(question)
    web_context = ""
    
    if search_results:
        web_context = fetch_web_content(search_results[0]['url'])
    
    # Ответ AI
    answer = process_with_ollama(question, web_context)
    
    return jsonify({
        'question': question,
        'answer': answer,
        'sources': search_results
    })

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Укажите query'}), 400
    
    results = search_web(query)
    return jsonify({'query': query, 'results': results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
