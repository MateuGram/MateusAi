import os
import json
import requests
from flask import Flask, request, Response, render_template_string, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

MISTRAL_API_KEY = "V8Ad82ZW8R5lF3qNkmSTQTkoC06FYiyh"
MODEL = "mistral-small-latest"   # быстрая бесплатная модель

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
    if not user_message:
        return "No message", 400

    # Получаем историю из сессии (вне генератора)
    history = session.get('history', [])
    history.append({"role": "user", "content": user_message})
    # Ограничим длину истории, чтобы не перегружать память
    history = history[-20:]

    system_prompt = (
        "Ты — MateusAI, дружелюбный и полезный ассистент. "
        "Отвечай на русском языке. Используй Markdown для форматирования: "
        "жирный, курсив, блоки кода с указанием языка, ссылки. "
        "Когда даёшь код, объясняй свои действия по шагам, показывай ход мыслей. "
        "Будь вежливым и помогай пользователю."
    )
    messages = [{"role": "system", "content": system_prompt}] + history

    # Функция-генератор не обращается к session, получает историю через замыкание
    def generate(history_before):
        full_content = ""
        try:
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
                    "max_tokens": 2048,          # увеличен для больших ответов
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
                            full_content += token
                            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    except Exception as e:
                        print("Ошибка парсинга чанка:", e)

                # После окончания генерации обновляем сессию с помощью функции, вызываемой после return
                # Но так как мы не можем сделать это внутри генератора (нет контекста запроса),
                # передадим историю обратно через специальное сообщение и обновим на стороне клиента?
                # Лучше обновить сессию после того, как генератор закончит работу.
                # Для этого мы можем вернуть полный ответ в конце и обновить сессию в вызывающем коде.
                # Но т.к. мы уже вне контекста, нужно передать результат наружу.
                # Сделаем так: сохраним полный ответ в замыкание, а после завершения генерации
                # (в том же потоке, но вне генератора) обновим сессию.
                # Для этого нам нужно, чтобы generate() вернул не только чанки, но и final_content.
                # Реализуем через возврат значения после итерации.
                # Для простоты: обновим сессию здесь, используя app.app_context().
                with app.app_context():
                    updated_history = history_before + [{"role": "assistant", "content": full_content}]
                    session['history'] = updated_history
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Ошибка: {str(e)}'})}\n\n"
        finally:
            # Сигнализируем о конце (клиент может закрыть соединение)
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

    # Обернём генератор, чтобы передать копию истории до обновления
    # Передаём в генератор текущую историю (без ответа ассистента)
    return Response(generate(history), mimetype="text/event-stream")

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('history', None)
    return {"status": "ok"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
