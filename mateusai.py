import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Твой API ключ
API_KEY = "cabb2fcef2e249fcb03c5cb80a47fb89.xfcCSfYXoLYnyDdZWoIwyY38"

# Простой HTML с чатом
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>MateusAI</title>
    <meta charset="utf-8">
    <style>
        body { margin: 0; padding: 20px; font-family: Arial; background: #1a1a1a; color: #fff; }
        .chat { max-width: 600px; margin: 0 auto; }
        .messages { height: 400px; overflow-y: auto; border: 1px solid #333; padding: 10px; margin-bottom: 10px; }
        .user { color: #4caf50; margin: 5px 0; }
        .bot { color: #fff; margin: 5px 0; }
        input { width: 80%; padding: 10px; background: #333; border: none; color: #fff; }
        button { width: 18%; padding: 10px; background: #4caf50; border: none; color: #fff; cursor: pointer; }
    </style>
</head>
<body>
    <div class="chat">
        <h2>MateusAI - Чат</h2>
        <div class="messages" id="messages"></div>
        <div>
            <input type="text" id="input" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') send()">
            <button onclick="send()">Отправить</button>
        </div>
    </div>

    <script>
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value;
            if (!msg) return;
            
            const messages = document.getElementById('messages');
            messages.innerHTML += `<div class="user">Вы: ${msg}</div>`;
            input.value = '';
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });
            
            const data = await response.json();
            messages.innerHTML += `<div class="bot">MateusAI: ${data.response}</div>`;
            messages.scrollTop = messages.scrollHeight;
        }
    </script>
</body>
</html>
'''

def call_ai_api(prompt):
    """Пытается вызвать разные AI API"""
    
    # Вариант 1: Ollama (если запущена локально)
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("response", "")
    except:
        pass
    
    # Вариант 2: OpenAI совместимый API
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    
    # Вариант 3: Простая локальная генерация (запасной вариант)
    responses = {
        "привет": "Привет! Как дела?",
        "как дела": "У меня всё отлично! А у тебя?",
        "что делаешь": "Общаюсь с тобой!",
        "пока": "Пока! До встречи!",
        "кто ты": "Я MateusAI - твой виртуальный помощник",
    }
    
    for key in responses:
        if key in prompt.lower():
            return responses[key]
    
    return f"Получил сообщение: '{prompt}'. Но API временно недоступен. Испольуй локальную версию."

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    ai_response = call_ai_api(user_message)
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)    <script>
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value;
            if (!msg) return;
            
            // Добавляем сообщение пользователя
            const messages = document.getElementById('messages');
            messages.innerHTML += `<div class="user">Вы: ${msg}</div>`;
            input.value = '';
            
            // Отправляем запрос
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });
            
            const data = await response.json();
            messages.innerHTML += `<div class="bot">MateusAI: ${data.response}</div>`;
            messages.scrollTop = messages.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    try:
        # Запрос к Ollama API
        response = requests.post(
            "https://api.ollama.ai/v1/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama2",
                "prompt": user_message,
                "max_tokens": 500,
                "temperature": 0.8
            },
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["text"].strip()
        else:
            ai_response = f"Ошибка API: {response.status_code}"
            
    except Exception as e:
        ai_response = f"Ошибка: {str(e)}"
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
