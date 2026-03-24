import os
import requests
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
app.secret_key = os.urandom(24)  # для сессий

MISTRAL_API_KEY = "V8Ad82ZW8R5lF3qNkmSTQTkoC06FYiyh"
MODEL = "mistral-tiny"

system_message = {
    "role": "system",
    "content": "Ты — Mateus AI, дружелюбный и умный помощник. Отвечай на русском языке, поддерживай контекст диалога. Используй Markdown для форматирования: жирный, курсив, блоки кода, ссылки."
}

# Читаем HTML
try:
    with open('index.html', 'r', encoding='utf-8') as f:
        HTML_TEMPLATE = f.read()
except:
    HTML_TEMPLATE = "<h1>Ошибка загрузки HTML</h1>"

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({"response": "Напиши что-нибудь!"})

    # Получаем историю из сессии (или создаём)
    if 'history' not in session:
        session['history'] = []
    
    history = session['history']
    # Добавляем новое сообщение пользователя в историю
    history.append({"role": "user", "content": user_message})
    
    # Оставляем только последние 10 сообщений, чтобы не перегружать API
    history = history[-10:]
    session['history'] = history

    try:
        # Формируем список сообщений для API Mistral
        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Добавляем системную инструкцию (по желанию)
        # messages.insert(0, {"role": "system", "content": "Ты дружелюбный помощник."})

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
                "max_tokens": 500
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            # Сохраняем ответ ассистента в историю
            history.append({"role": "assistant", "content": ai_response})
            session['history'] = history
        else:
            ai_response = f"❌ Ошибка API: {response.status_code}"
            if response.status_code == 401:
                ai_response = "❌ Неверный ключ Mistral AI."
            elif response.status_code == 429:
                ai_response = "⏳ Превышен лимит запросов."

    except Exception as e:
        ai_response = f"❌ Ошибка: {str(e)}"

    return jsonify({"response": ai_response})

@app.route('/reset', methods=['POST'])
def reset():
    """Сброс истории диалога."""
    session.pop('history', None)
    return jsonify({"status": "ok", "message": "История очищена"})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "ok",
        "model": MODEL,
        "api_key_configured": bool(MISTRAL_API_KEY)
    })
