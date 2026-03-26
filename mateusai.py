import os
import json
import requests
from flask import Flask, request, Response, render_template_string, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

MISTRAL_API_KEY = "V8Ad82ZW8R5lF3qNkmSTQTkoC06FYiyh"
MODEL = "mistral-small-latest"

# Загружаем HTML
try:
    with open('index.html', 'r', encoding='utf-8') as f:
        HTML_TEMPLATE = f.read()
except:
    HTML_TEMPLATE = "<h1>Ошибка загрузки HTML</h1>"

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Потоковый чат с Mistral через Server-Sent Events"""
    data = request.json
    user_message = data.get('message', '')
    if not user_message:
        return "No message", 400

    # Получаем историю сессии (опционально, можно хранить и здесь)
    if 'history' not in session:
        session['history'] = []
    history = session['history']
    history.append({"role": "user", "content": user_message})
    # Оставляем последние 20
    history = history[-20:]
    session['history'] = history

    # Системный промпт с просьбой объяснять ход мыслей
    system_prompt = (
        "Ты — MateusAI, дружелюбный и полезный ассистент. "
        "Отвечай на русском языке. Используй Markdown для форматирования. "
        "Когда даёшь код, объясняй, что ты делаешь, показывай ход мыслей по шагам. "
        "Если просят написать код — пиши его с указанием языка. "
        "Будь вежливым и помогай пользователю."
    )

    # Собираем сообщения
    messages = [{"role": "system", "content": system_prompt}] + history

    # Функция-генератор для SSE
    def generate():
        # Отправляем начало стрима
        yield f"data: {json.dumps({'type': 'start'})}\n\n"

        try:
            # Открываем потоковое соединение с Mistral
            with requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 800,
                    "stream": True   # включаем стриминг
                },
                stream=True,
                timeout=120
            ) as response:
                if response.status_code != 200:
                    error_msg = f"❌ Ошибка API: {response.status_code}"
                    yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                    return

                # Читаем поток построчно
                full_content = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    # Убираем "data: " в начале
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    if line_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line_str)
                        # Извлекаем токен
                        delta = chunk['choices'][0]['delta']
                        if 'content' in delta:
                            token = delta['content']
                            full_content += token
                            # Отправляем токен клиенту
                            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    except Exception as e:
                        print("Ошибка парсинга чанка:", e)

                # Сохраняем полный ответ в историю
                history.append({"role": "assistant", "content": full_content})
                session['history'] = history

                yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Ошибка: {str(e)}'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('history', None)
    return {"status": "ok"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
