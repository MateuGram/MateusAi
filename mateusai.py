import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Твой Hugging Face токен
HF_TOKEN = "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"

# Доступные модели
MODELS = {
    "blenderbot": "facebook/blenderbot-400M-distill",
    "gpt2": "gpt2",
    "flan-t5": "google/flan-t5-base",
    "dialoGPT": "microsoft/DialoGPT-medium"
}

current_model = "facebook/blenderbot-400M-distill"

HTML = '''
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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
            margin-bottom: 10px;
        }
        
        .model-selector {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        
        .model-selector select {
            padding: 8px 15px;
            border-radius: 20px;
            border: none;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 14px;
            cursor: pointer;
            outline: none;
        }
        
        .model-selector select option {
            background: #764ba2;
            color: white;
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
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
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
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .message-time {
            font-size: 10px;
            margin-top: 5px;
            opacity: 0.6;
            text-align: right;
        }
        
        .typing-indicator {
            display: flex;
            padding: 12px 18px;
            background: white;
            border-radius: 20px;
            border-bottom-left-radius: 5px;
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
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
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
        
        .badge {
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
            <h1>MateusAI <span class="badge">Hugging Face</span></h1>
            <p>ИИ с доступом к разным моделям</p>
            <div class="model-selector">
                <select id="modelSelect" onchange="changeModel()">
                    <option value="facebook/blenderbot-400M-distill">BlenderBot (лучший для чата)</option>
                    <option value="gpt2">GPT-2 (текст)</option>
                    <option value="google/flan-t5-base">FLAN-T5 (универсальный)</option>
                    <option value="microsoft/DialoGPT-medium">DialoGPT (диалоги)</option>
                </select>
            </div>
        </div>
        
        <div class="chat-messages" id="messages">
            <div class="message bot-message">
                <div class="message-content">
                    👋 Привет! Я MateusAI. Выбери модель и задавай вопросы!
                    <div class="message-time">только что</div>
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Напиши сообщение..." onkeypress="if(event.key === 'Enter') sendMessage()">
            <button onclick="sendMessage()" id="sendBtn">Отправить</button>
        </div>
    </div>

    <script>
        let isWaiting = false;
        
        async function changeModel() {
            const select = document.getElementById('modelSelect');
            const model = select.value;
            
            const response = await fetch('/set_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model: model})
            });
            
            addMessage(`✅ Модель изменена на ${select.options[select.selectedIndex].text}`, false);
        }
        
        function addMessage(text, isUser) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            div.innerHTML = `
                <div class="message-content">
                    ${text}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function showTyping() {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message bot-message';
            div.id = 'typing';
            div.innerHTML = `
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message || isWaiting) return;
            
            addMessage(message, true);
            input.value = '';
            
            showTyping();
            isWaiting = true;
            document.getElementById('sendBtn').disabled = true;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, false);
                
            } catch (error) {
                hideTyping();
                addMessage('❌ Ошибка. Попробуй ещё раз.', false);
            }
            
            isWaiting = false;
            document.getElementById('sendBtn').disabled = false;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/set_model', methods=['POST'])
def set_model():
    global current_model
    data = request.json
    current_model = data.get('model', current_model)
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['POST'])
def chat():
    global current_model
    data = request.json
    user_message = data.get('message', '')
    
    try:
        if 'blenderbot' in current_model:
            payload = {"inputs": {"text": user_message}}
        elif 't5' in current_model:
            payload = {"inputs": f"answer: {user_message}"}
        else:
            payload = {"inputs": user_message}
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{current_model}",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    if 'generated_text' in result[0]:
                        ai_response = result[0]['generated_text']
                    else:
                        ai_response = str(result[0])
                else:
                    ai_response = str(result[0])
            elif isinstance(result, dict) and 'generated_text' in result:
                ai_response = result['generated_text']
            else:
                ai_response = str(result)
                
        elif response.status_code == 503:
            ai_response = "⏳ Модель загружается... Подожди 10 секунд и попробуй снова."
        else:
            ai_response = f"❌ Ошибка API: {response.status_code}"
            
    except Exception as e:
        ai_response = f"❌ Ошибка: {str(e)}"
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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
            margin-bottom: 10px;
        }
        
        .model-selector {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        
        .model-selector select {
            padding: 8px 15px;
            border-radius: 20px;
            border: none;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 14px;
            cursor: pointer;
            outline: none;
        }
        
        .model-selector select option {
            background: #764ba2;
            color: white;
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
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
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
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .message-time {
            font-size: 10px;
            margin-top: 5px;
            opacity: 0.6;
            text-align: right;
        }
        
        .typing-indicator {
            display: flex;
            padding: 12px 18px;
            background: white;
            border-radius: 20px;
            border-bottom-left-radius: 5px;
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
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
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
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            background: #4caf50;
            color: white;
            border-radius: 12px;
            font-size: 11px;
            margin-left: 10px;
        }
        
        .error-message {
            color: #f44336;
            font-size: 12px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>MateusAI <span class="badge">Hugging Face</span></h1>
            <p>ИИ с доступом к разным моделям</p>
            <div class="model-selector">
                <select id="modelSelect" onchange="changeModel()">
                    <option value="facebook/blenderbot-400M-distill">BlenderBot (лучший для чата)</option>
                    <option value="gpt2">GPT-2 (текст)</option>
                    <option value="google/flan-t5-base">FLAN-T5 (универсальный)</option>
                    <option value="microsoft/DialoGPT-medium">DialoGPT (диалоги)</option>
                </select>
            </div>
        </div>
        
        <div class="chat-messages" id="messages">
            <div class="message bot-message">
                <div class="message-content">
                    👋 Привет! Я MateusAI. Выбери модель и задавай вопросы!
                    <div class="message-time">только что</div>
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Напиши сообщение..." onkeypress="if(event.key === 'Enter') sendMessage()">
            <button onclick="sendMessage()" id="sendBtn">Отправить</button>
        </div>
    </div>

    <script>
        let isWaiting = false;
        
        async function changeModel() {
            const select = document.getElementById('modelSelect');
            const model = select.value;
            
            const response = await fetch('/set_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model: model})
            });
            
            addMessage(`✅ Модель изменена на ${select.options[select.selectedIndex].text}`, false);
        }
        
        function addMessage(text, isUser) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            div.innerHTML = `
                <div class="message-content">
                    ${text}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function showTyping() {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message bot-message';
            div.id = 'typing';
            div.innerHTML = `
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            
            if (!message || isWaiting) return;
            
            addMessage(message, true);
            input.value = '';
            
            showTyping();
            isWaiting = true;
            document.getElementById('sendBtn').disabled = true;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, false);
                
            } catch (error) {
                hideTyping();
                addMessage('❌ Ошибка. Попробуй ещё раз.', false);
            }
            
            isWaiting = false;
            document.getElementById('sendBtn').disabled = false;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/set_model', methods=['POST'])
def set_model():
    global current_model
    data = request.json
    current_model = data.get('model', current_model)
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['POST'])
def chat():
    global current_model
    data = request.json
    user_message = data.get('message', '')
    
    try:
        # Разные форматы для разных моделей
        if 'blenderbot' in current_model:
            payload = {"inputs": {"text": user_message}}
        elif 't5' in current_model:
            payload = {"inputs": f"answer: {user_message}"}
        else:
            payload = {"inputs": user_message}
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{current_model}",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    if 'generated_text' in result[0]:
                        ai_response = result[0]['generated_text']
                    else:
                        ai_response = str(result[0])
                else:
                    ai_response = str(result[0])
            elif isinstance(result, dict) and 'generated_text' in result:
                ai_response = result['generated_text']
            else:
                ai_response = str(result)
                
        elif response.status_code == 503:
            ai_response = "⏳ Модель загружается... Подожди 10 секунд и попробуй снова."
        else:
            ai_response = f"❌ Ошибка API: {response.status_code}"
            
    except Exception as e:
        ai_response = f"❌ Ошибка: {str(e)}"
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)            border: 1px solid #404040; 
            padding: 10px; 
            margin-bottom: 10px; 
        }
        .user { 
            color: #4caf50; 
            margin: 5px 0; 
            text-align: right; 
        }
        .bot { 
            color: white; 
            margin: 5px 0; 
            text-align: left; 
        }
        input { 
            width: 80%; 
            padding: 10px; 
            background: #404040; 
            border: none; 
            color: white; 
        }
        button { 
            width: 18%; 
            padding: 10px; 
            background: #4caf50; 
            border: none; 
            color: white; 
            cursor: pointer; 
        }
    </style>
</head>
<body>
    <div class="chat">
        <h2>MateusAI</h2>
        <div class="messages" id="messages">
            <div class="bot">MateusAI: Привет! Я MateusAI. Задавай вопросы!</div>
        </div>
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

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{CURRENT_MODEL}",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": user_message},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and 'generated_text' in result[0]:
                    ai_response = result[0]['generated_text']
                else:
                    ai_response = str(result[0])
            else:
                ai_response = str(result)
        else:
            ai_response = f"Ошибка API: {response.status_code}"
            
    except Exception as e:
        ai_response = f"Ошибка: {str(e)}"
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
