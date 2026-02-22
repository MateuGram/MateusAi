import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Твой Hugging Face токен
HF_TOKEN = "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"

# Модель
CURRENT_MODEL = "facebook/blenderbot-400M-distill"

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>MateusAI</title>
    <meta charset="utf-8">
    <style>
        body { 
            margin: 0; 
            padding: 20px; 
            font-family: Arial; 
            background: #1a1a1a; 
            color: white; 
        }
        .chat { 
            max-width: 600px; 
            margin: 0 auto; 
            background: #2d2d2d; 
            border-radius: 10px; 
            padding: 20px; 
        }
        .messages { 
            height: 400px; 
            overflow-y: auto; 
            border: 1px solid #404040; 
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
