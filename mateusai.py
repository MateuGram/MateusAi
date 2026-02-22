import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Твой Hugging Face токен
HF_TOKEN = "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"

# Читаем HTML файл из корневой папки
try:
    with open('index.html', 'r', encoding='utf-8') as file:
        HTML_TEMPLATE = file.read()
    print("✅ HTML файл успешно загружен")
except Exception as e:
    print(f"❌ Ошибка загрузки HTML: {e}")
    HTML_TEMPLATE = "<h1>Ошибка загрузки HTML</h1>"

# Переменная для хранения текущей модели
current_model = "facebook/blenderbot-400M-distill"

@app.route('/')
def home():
    """Отображает главную страницу с чатом."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/set_model', methods=['POST'])
def set_model():
    """Изменяет текущую модель."""
    global current_model
    data = request.json
    new_model = data.get('model')
    if new_model:
        current_model = new_model
        print(f"🔄 Модель изменена на: {current_model}")
    return jsonify({"status": "ok", "model": current_model})

@app.route('/chat', methods=['POST'])
def chat():
    """Обрабатывает сообщения пользователя и возвращает ответ от AI."""
    global current_model
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"response": "Напиши что-нибудь!"})

    print(f"📨 Запрос к {current_model}: {user_message}")

    try:
        # Проверка токена
        if not HF_TOKEN:
            return jsonify({"response": "❌ Ошибка: Не указан Hugging Face токен!"})

        # Запрос к Hugging Face
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{current_model}",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": user_message},
            timeout=30
        )
        
        print(f"📥 Статус ответа: {response.status_code}")

        # Обработка ответа
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
                
        elif response.status_code == 401:
            ai_response = "❌ Ошибка авторизации. Проверь Hugging Face токен!"
        elif response.status_code == 503:
            ai_response = "⏳ Модель загружается... Подожди 10 секунд и попробуй снова."
        else:
            ai_response = f"❌ Ошибка API: {response.status_code}"

    except requests.exceptions.ConnectionError:
        ai_response = "❌ Ошибка соединения с Hugging Face API."
    except requests.exceptions.Timeout:
        ai_response = "⏳ Превышено время ожидания."
    except Exception as e:
        ai_response = f"❌ Ошибка: {str(e)}"

    return jsonify({"response": ai_response})

@app.route('/test', methods=['GET'])
def test():
    """Проверка работы сервера."""
    return jsonify({
        "status": "ok",
        "message": "Сервер работает!",
        "current_model": current_model,
        "token_configured": bool(HF_TOKEN)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    print(f"🤖 Текущая модель: {current_model}")
    print(f"🔑 Токен настроен: {bool(HF_TOKEN)}")
    app.run(host='0.0.0.0', port=port, debug=False)
