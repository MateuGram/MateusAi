import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Твой Hugging Face токен
HF_TOKEN = "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"

# Работающие бесплатные модели Hugging Face
# DialoGPT больше не работает, используем другие
MODELS = {
    "gpt2": "gpt2",  # Базовая GPT-2
    "blender": "facebook/blenderbot-400M-distill",  # Чат-бот от Facebook
    "t5": "google/flan-t5-small",  # Универсальная модель
    "dialogpt": "microsoft/DialoGPT-small"  # Маленькая версия
}

# Выбираем модель (можно менять)
CURRENT_MODEL = MODELS["blender"]  # Facebook Blenderbot - хорошо для чата

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>MateusAI - Чат с Hugging Face</title>
    <meta charset="utf-8">
    <style>
        body { 
            margin: 0; 
            padding: 20px; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chat { 
            max-width: 600px; 
            width: 100%;
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h2 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0;
            opacity: 0.9;
            font-size: 14px;
        }
        .model-selector {
            margin-top: 10px;
        }
        .model-selector select {
            padding: 5px;
            border-radius: 5px;
            border: none;
            background: rgba(255,255,255,0.2);
            color: white;
            cursor: pointer;
        }
        .model-selector select option {
            background: #764ba2;
            color: white;
        }
        .messages { 
            height: 400px; 
            overflow-y: auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
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
            padding: 10px 15px;
            border-radius: 18px;
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
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        input { 
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #eee;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        input:focus {
            border-color: #667eea;
        }
        button { 
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .typing {
            display: flex;
            padding: 10px 15px;
            background: white;
            border-radius: 18px;
            border-bottom-left-radius: 5px;
            width: fit-content;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            background: #ff9800;
            color: white;
            border-radius: 12px;
            font-size: 11px;
            margin-left: 10px;
        }
        .error {
            color: #f44336;
            font-size: 12px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="chat">
        <div class="header">
            <h2>MateusAI <span class="badge">Hugging Face</span></h2>
            <p>Чат с искусственным интеллектом</p>
            <div class="model-selector">
                <select id="modelSelect" onchange="changeModel()">
                    <option value="facebook/blenderbot-400M-distill">BlenderBot (лучший для чата)</option>
                    <option value="gpt2">GPT-2 (текст)</option>
                    <option value="google/flan-t5-small">FLAN-T5 (универсальный)</option>
                    <option value="microsoft/DialoGPT-small">DialoGPT (диалоги)</option>
                </select>
            </div>
        </div>
        
        <div class="messages" id="messages">
            <div class="message bot-message">
                <div class="message-content">
                    👋 Привет! Я MateusAI. Задавай любые вопросы!
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="input" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') send()">
            <button onclick="send()" id="sendBtn">Отправить</button>
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
        }
        
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value.trim();
            if (!msg || isWaiting) return;
            
            addMessage(msg, true);
            input.value = '';
            
            showTyping();
            isWaiting = true;
            document.getElementById('sendBtn').disabled = true;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, false);
                
            } catch (error) {
                hideTyping();
                addMessage('Извини, произошла ошибка. Попробуй ещё раз.', false);
            }
            
            isWaiting = false;
            document.getElementById('sendBtn').disabled = false;
        }
        
        function addMessage(text, isUser) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
            
            div.innerHTML = `
                <div class="message-content">
                    ${text}
                    <div style="font-size:10px; opacity:0.6; margin-top:5px; text-align:right">${time}</div>
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
            div.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
    </script>
</body>
</html>
'''

# Хранилище текущей модели
current_model = CURRENT_MODEL

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/set_model', methods=['POST'])
def set_model():
    global current_model
    data = request.json
    current_model = data.get('model', current_model)
    return jsonify({"status": "ok", "model": current_model})

@app.route('/chat', methods=['POST'])
def chat():
    global current_model
    data = request.json
    user_message = data.get('message', '')
    
    try:
        # Для разных моделей разный формат запроса
        if "blender" in current_model:
            # BlenderBot требует особый формат
            payload = {
                "inputs": {
                    "past_user_inputs": [],
                    "generated_responses": [],
                    "text": user_message
                }
            }
        elif "t5" in current_model:
            # T5 модели
            payload = {
                "inputs": f"answer: {user_message}",
                "parameters": {
                    "max_length": 150,
                    "temperature": 0.7
                }
            }
        else:
            # Стандартный формат для GPT и DialoGPT
            payload = {
                "inputs": user_message,
                "parameters": {
                    "max_length": 150,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
        
        # Запрос к Hugging Face
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{current_model}",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Обрабатываем разные форматы ответов
            if isinstance(result, list):
                if len(result) > 0:
                    if isinstance(result[0], dict):
                        if 'generated_text' in result[0]:
                            ai_response = result[0]['generated_text']
                        elif 'generated_texts' in result[0]:
                            ai_response = result[0]['generated_texts'][0]
                        else:
                            ai_response = str(result[0])
                    else:
                        ai_response = str(result[0])
                else:
                    ai_response = "Пустой ответ"
            elif isinstance(result, dict):
                if 'generated_text' in result:
                    ai_response = result['generated_text']
                elif 'error' in result:
                    ai_response = f"Ошибка: {result['error']}"
                else:
                    ai_response = str(result)
            else:
                ai_response = str(result)
                
        elif response.status_code == 503:
            ai_response = "Модель загружается... Подожди 10-20 секунд и попробуй снова."
        else:
            ai_response = f"Ошибка API: {response.status_code}"
            
    except requests.exceptions.Timeout:
        ai_response = "Превышено время ожидания. Попробуй ещё раз."
    except Exception as e:
        ai_response = f"Ошибка: {str(e)}"
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 MateusAI запущен на порту {port}")
    print(f"🤖 Модель: {current_model}")
    print("💡 Если модель не отвечает, подожди 10-20 секунд - она загружается")
    app.run(host='0.0.0.0', port=port)            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h2 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0;
            opacity: 0.9;
            font-size: 14px;
        }
        .messages { 
            height: 400px; 
            overflow-y: auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
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
            padding: 10px 15px;
            border-radius: 18px;
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
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        input { 
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #eee;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        input:focus {
            border-color: #667eea;
        }
        button { 
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .typing {
            display: flex;
            padding: 10px 15px;
            background: white;
            border-radius: 18px;
            border-bottom-left-radius: 5px;
            width: fit-content;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
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
        .model-info {
            font-size: 12px;
            margin-top: 5px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="chat">
        <div class="header">
            <h2>MateusAI <span class="badge">Hugging Face</span></h2>
            <p>Чат с искусственным интеллектом</p>
            <div class="model-info" id="modelInfo">Модель: {{ model }}</div>
        </div>
        
        <div class="messages" id="messages">
            <div class="message bot-message">
                <div class="message-content">
                    👋 Привет! Я MateusAI на базе Hugging Face. 
                    Задавай любые вопросы!
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="input" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') send()">
            <button onclick="send()" id="sendBtn">Отправить</button>
        </div>
    </div>

    <script>
        let isWaiting = false;
        
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value.trim();
            if (!msg || isWaiting) return;
            
            // Добавляем сообщение пользователя
            addMessage(msg, true);
            input.value = '';
            
            // Показываем печатание
            showTyping();
            isWaiting = true;
            document.getElementById('sendBtn').disabled = true;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, false);
                
            } catch (error) {
                hideTyping();
                addMessage('Извини, произошла ошибка. Попробуй ещё раз.', false);
            }
            
            isWaiting = false;
            document.getElementById('sendBtn').disabled = false;
        }
        
        function addMessage(text, isUser) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            
            const time = new Date().toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
            
            div.innerHTML = `
                <div class="message-content">
                    ${text}
                    <div style="font-size:10px; opacity:0.6; margin-top:5px; text-align:right">${time}</div>
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
            div.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML, model=MODEL)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    try:
        # Запрос к Hugging Face Inference API
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{MODEL}",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "inputs": user_message,
                "parameters": {
                    "max_length": 150,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Обрабатываем разные форматы ответов
            if isinstance(result, list):
                if len(result) > 0:
                    if isinstance(result[0], dict) and 'generated_text' in result[0]:
                        ai_response = result[0]['generated_text']
                    elif isinstance(result[0], str):
                        ai_response = result[0]
                    else:
                        ai_response = str(result[0])
                else:
                    ai_response = "Пустой ответ от модели"
            elif isinstance(result, dict) and 'error' in result:
                ai_response = f"Ошибка модели: {result['error']}"
            else:
                ai_response = str(result)
                
        elif response.status_code == 503:
            ai_response = "Модель загружается... Попробуй через пару секунд."
        else:
            ai_response = f"Ошибка API: {response.status_code}"
            
    except requests.exceptions.Timeout:
        ai_response = "Превышено время ожидания. Попробуй ещё раз."
    except Exception as e:
        ai_response = f"Ошибка: {str(e)}"
    
    return jsonify({"response": ai_response})

@app.route('/models', methods=['GET'])
def list_models():
    """Получить список доступных моделей"""
    try:
        response = requests.get(
            "https://api-inference.huggingface.co/models",
            headers={"Authorization": f"Bearer {HF_TOKEN}"}
        )
        if response.status_code == 200:
            models = [m['modelId'] for m in response.json()[:10]]
            return jsonify({"models": models})
    except:
        pass
    return jsonify({"error": "Не удалось получить список моделей"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 MateusAI запущен на порту {port}")
    print(f"🤖 Используется модель: {MODEL}")
    print(f"🔑 Hugging Face токен: {HF_TOKEN[:10]}...")
    app.run(host='0.0.0.0', port=port)
