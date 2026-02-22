import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Твой Hugging Face токен
HF_TOKEN = "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"

# Переменная для хранения текущей модели
current_model = "facebook/blenderbot-400M-distill"

@app.route('/')
def home():
    """Отображает главную страницу с чатом."""
    return render_template('index.html')

@app.route('/set_model', methods=['POST'])
def set_model():
    """Изменяет текущую модель."""
    global current_model
    data = request.json
    new_model = data.get('model')
    if new_model:
        current_model = new_model
    return jsonify({"status": "ok", "model": current_model})

@app.route('/chat', methods=['POST'])
def chat():
    """Обрабатывает сообщения пользователя и возвращает ответ от AI."""
    global current_model
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"response": "Напиши что-нибудь!"})

    # Настройка payload в зависимости от модели
    if 'blenderbot' in current_model:
        payload = {"inputs": {"text": user_message}}
    elif 't5' in current_model:
        payload = {"inputs": f"answer: {user_message}"}
    else:
        payload = {"inputs": user_message}

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    api_url = f"https://api-inference.huggingface.co/models/{current_model}"

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        result = response.json()

        ai_response = "Извини, не могу понять ответ модели."
        if response.status_code == 200:
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if isinstance(first_item, dict):
                    if 'generated_text' in first_item:
                        generated = first_item['generated_text']
                        if isinstance(generated, dict) and 'text' in generated:
                            ai_response = generated['text']
                        elif isinstance(generated, str):
                            ai_response = generated
                elif isinstance(first_item, str):
                    ai_response = first_item
            elif isinstance(result, dict) and 'generated_text' in result:
                ai_response = result['generated_text']
            elif isinstance(result, str):
                ai_response = result
        elif response.status_code == 503:
            ai_response = "⏳ Модель загружается... Подожди 10 секунд и попробуй снова."
        else:
            ai_response = f"❌ Ошибка API: {response.status_code}"

    except requests.exceptions.Timeout:
        ai_response = "⏳ Превышено время ожидания. Модель может быть перегружена."
    except Exception as e:
        ai_response = f"❌ Ошибка: {str(e)}"

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
