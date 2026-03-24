import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Твой ключ Mistral AI
MISTRAL_API_KEY = "V8Ad82ZW8R5lF3qNkmSTQTkoC06FYiyh"

# Читаем HTML из корневой папки
try:
    with open('index.html', 'r', encoding='utf-8') as f:
        HTML_TEMPLATE = f.read()
    print("✅ index.html загружен")
except Exception as e:
    print(f"❌ Ошибка загрузки HTML: {e}")
    HTML_TEMPLATE = "<h1>Ошибка загрузки HTML</h1>"

# Модель Mistral (можно поменять на "mistral-small-latest" или "mistral-medium-latest")
MODEL = "mistral-tiny"  # Быстрая и бесплатная

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Отправляет сообщение в Mistral AI и возвращает ответ."""
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"response": "Напиши что-нибудь!"})

    try:
        # Запрос к Mistral API
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
        else:
            ai_response = f"❌ Ошибка API: {response.status_code}"
            if response.status_code == 401:
                ai_response = "❌ Неверный ключ Mistral AI. Проверь его."
            elif response.status_code == 429:
                ai_response = "⏳ Превышен лимит запросов. Подожди немного."

    except requests.exceptions.Timeout:
        ai_response = "⏳ Превышено время ожидания. Попробуй ещё раз."
    except Exception as e:
        ai_response = f"❌ Ошибка: {str(e)}"

    return jsonify({"response": ai_response})

@app.route('/test', methods=['GET'])
def test():
    """Проверка работоспособности."""
    return jsonify({
        "status": "ok",
        "message": "Сервер работает с Mistral AI",
        "model": MODEL,
        "api_key_configured": bool(MISTRAL_API_KEY)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    print(f"🤖 Модель Mistral: {MODEL}")
    print(f"🔑 Ключ настроен: {bool(MISTRAL_API_KEY)}")
    app.run(host='0.0.0.0', port=port)
