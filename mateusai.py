import os
import requests
import json
import time
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# API ключ Ollama
OLLAMA_API_KEY = "cabb2fcef2e249fcb03c5cb80a47fb89.xfcCSfYXoLYnyDdZWoIwyY38"
OLLAMA_URL = "https://api.ollama.ai/v1/completions"

# История диалога
conversation_history = []

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
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            background: #4caf50;
            color: white;
            border-radius: 12px;
            font-size: 11px;
            margin-left: 10px;
        }
        
        .internet-badge {
            display: inline-block;
            padding: 3px 8px;
            background: #ff9800;
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
            <h1>MateusAI 
                <span class="status-badge">Online</span>
                <span class="internet-badge">Internet</span>
            </h1>
            <p>ИИ с доступом в интернет • Задавай любые вопросы</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                <div class="message-content">
                    👋 Привет! Я MateusAI - твой умный помощник с доступом в интернет.<br><br>
                    Я могу:<br>
                    • Отвечать на любые вопросы<br>
                    • Искать информацию в интернете<br>
                    • Помогать с задачами<br>
                    • Вести обычный диалог<br><br>
                    Чем я могу помочь? 🌟
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
        
        function addMessage(text, isUser) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${text}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
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
                // Отправляем запрос к API
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Убираем индикатор печати
                removeTypingIndicator();
                
                // Добавляем ответ бота
                addMessage(data.response, false);
                
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
        
        return text[:2000]
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
        for g in soup.find_all('div', class_='g')[:2]:
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

def needs_internet_search(message):
    """Проверяет, нужен ли поиск в интернете"""
    search_keywords = ['найди', 'поищи', 'сколько', 'кто такой', 'что такое', 
                      'новости', 'погода', 'курс', 'цена', 'как', 'почему',
                      'когда', 'где', 'последние', 'свежие', 'сегодня']
    
    message_lower = message.lower()
    for keyword in search_keywords:
        if keyword in message_lower:
            return True
    return False

def get_ai_response(message):
    """Получение ответа от AI"""
    global conversation_history
    
    # Добавляем сообщение в историю
    conversation_history.append({"role": "user", "content": message})
    
    # Проверяем, нужен ли поиск
    if needs_internet_search(message):
        search_results = search_web(message)
        web_context = ""
        
        if search_results:
            web_context = fetch_web_content(search_results[0]['url'])
            context = f"Вот информация из интернета по запросу: {web_context}\n\n"
        else:
            context = "Не удалось найти информацию в интернете.\n\n"
    else:
        context = ""
        search_results = []
    
    try:
        # Формируем промпт с контекстом диалога
        history_text = ""
        for msg in conversation_history[-6:]:  # Последние 6 сообщений
            role = "Человек" if msg["role"] == "user" else "Ты"
            history_text += f"{role}: {msg['content']}\n"
        
        full_prompt = f"""Ты дружелюбный AI помощник MateusAI. Отвечай как человек, поддерживай диалог.
        
История диалога:
{history_text}

{context}Твой ответ (естественно, по-русски):"""

        headers = {
            'Authorization': f'Bearer {OLLAMA_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "llama2",
            "prompt": full_prompt,
            "max_tokens": 300,
            "temperature": 0.8
        }
        
        response = requests.post(OLLAMA_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            ai_response = response.json().get('choices', [{}])[0].get('text', '')
            if not ai_response:
                ai_response = get_fallback_response(message)
        else:
            ai_response = get_fallback_response(message)
            
    except:
        ai_response = get_fallback_response(message)
    
    # Добавляем ответ в историю
    conversation_history.append({"role": "assistant", "content": ai_response})
    
    return ai_response

def get_fallback_response(message):
    """Запасные ответы если API недоступен"""
    message_lower = message.lower()
    
    # Приветствия
    if message_lower in ['привет', 'здравствуй', 'хай', 'hello', 'hi']:
        return "Привет! Как дела? Чем могу помочь?"
    
    # Как дела
    if 'как дела' in message_lower:
        return "У меня всё отлично! Рад общаться с тобой. А у тебя как?"
    
    # Что делаешь
    if 'что делаешь' in message_lower:
        return "Общаюсь с тобой и помогаю с вопросами! Есть что-то интересное?"
    
    # Пока/до свидания
    if message_lower in ['пока', 'до свидания', 'bye']:
        return "Пока! Буду рад снова помочь. Обращайся!"
    
    # Спасибо
    if 'спасибо' in message_lower:
        return "Пожалуйста! Рад помочь. Ещё что-то?"
    
    # Короткие сообщения
    if len(message) < 5:
        return "Да? Расскажи подробнее, я слушаю!"
    
    if '?' in message:
        return "Интересный вопрос! Дай подумать... Возможно, мне нужно поискать в интернете. Могу я поискать информацию для тебя?"
    
    return f"Понял тебя! Расскажи подробнее о '{message}', чтобы я мог лучше помочь."

@app.route('/')
def home():
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M")
    return render_template_string(HTML_TEMPLATE, current_time=current_time)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Укажите сообщение'}), 400
    
    response = get_ai_response(message)
    
    return jsonify({
        'response': response
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
