import os
import time
import requests
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

MISTRAL_API_KEY = "V8Ad82ZW8R5lF3qNkmSTQTkoC06FYiyh"
MODEL = "mistral-small-latest"   # более быстрая модель
TIMEOUT = 1000                     # увеличенный таймаут
RETRIES = 1                      # количество повторных попыток

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

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({"response": "Напиши что-нибудь!"})

    # История диалога
    if 'history' not in session:
        session['history'] = []
    history = session['history']
    history.append({"role": "user", "content": user_message})
    history = history[-20:]  # храним последние 20 сообщений

    # Системный промпт
    system_prompt = (
        "Ты — MateusAI, дружелюбный и полезный ассистент. "
        "Отвечай на русском языке. Используй Markdown для форматирования: "
        "жирный, курсив, блоки кода с указанием языка программирования, ссылки. "
        "Если просят написать код — оформляй его в тройные бэктики с указанием языка. "
        "Будь вежливым и помогай пользователю."
    )
    messages = [{"role": "system", "content": system_prompt}] + history

    # Пытаемся отправить запрос с повторными попытками при таймауте
    ai_response = None
    for attempt in range(RETRIES + 1):
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 800
                },
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                break
            else:
                # Логируем ошибку
                error_detail = ""
                try:
                    error_json = response.json()
                    error_detail = f" – {error_json.get('error', {}).get('message', '')}"
                except:
                    pass
                ai_response = f"❌ Ошибка API: {response.status_code}{error_detail}"
                print(f"API error: {response.status_code} – {response.text}")
                break   # не повторяем при ошибке 4xx, только при таймауте

        except requests.exceptions.Timeout:
            print(f"⏳ Таймаут, попытка {attempt+1} из {RETRIES+1}")
            if attempt == RETRIES:
                ai_response = "⏳ Превышено время ожидания. Попробуй ещё раз."
            else:
                time.sleep(2)  # пауза перед повторной попыткой
                continue
        except Exception as e:
            ai_response = f"❌ Ошибка: {str(e)}"
            print(f"Exception: {e}")
            break

    if ai_response is None:
        ai_response = "❌ Не удалось получить ответ"

    # Сохраняем ответ в историю
    history.append({"role": "assistant", "content": ai_response})
    session['history'] = history

    return jsonify({"response": ai_response})

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('history', None)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
