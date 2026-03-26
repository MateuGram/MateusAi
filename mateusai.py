import os
import json
import requests
from flask import Flask, request, Response, render_template_string

app = Flask(__name__)

MISTRAL_API_KEY = "V8Ad82ZW8R5lF3qNkmSTQTkoC06FYiyh"
MODEL = "mistral-small-latest"

try:
    with open('index.html', 'r', encoding='utf-8') as f:
        HTML_TEMPLATE = f.read()
    print("✅ index.html loaded")
except Exception as e:
    print(f"❌ Error loading index.html: {e}")
    HTML_TEMPLATE = "<h1>Error loading HTML</h1>"

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    data = request.json
    user_message = data.get('message', '')
    history = data.get('history', [])   # клиент присылает всю историю

    if not user_message:
        return "No message", 400

    # Добавляем текущее сообщение пользователя
    messages = history + [{"role": "user", "content": user_message}]

    system_prompt = (
        "Ты — MateusAI, дружелюбный и полезный ассистент. "
        "Отвечай на русском языке. Используй Markdown для форматирования: "
        "жирный, курсив, блоки кода с указанием языка, ссылки. "
        "Когда даёшь код, объясняй свои действия по шагам, показывай ход мыслей. "
        "Будь вежливым и помогай пользователю."
    )
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    def generate():
        try:
            with requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": full_messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "stream": True
                },
                stream=True,
                timeout=120
            ) as response:
                if response.status_code != 200:
                    error_msg = f"❌ Ошибка API: {response.status_code}"
                    yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                    return

                for line in response.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    if line_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line_str)
                        delta = chunk['choices'][0]['delta']
                        if 'content' in delta:
                            token = delta['content']
                            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    except Exception as e:
                        print("Ошибка парсинга чанка:", e)

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Ошибка: {str(e)}'})}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route('/reset', methods=['POST'])
def reset():
    return {"status": "ok"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
