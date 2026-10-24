import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

SITE_KNOWLEDGE = """
تو دستیار هوشمند سایت زهرا جعفریان هستی.
سایت درباره شعر و ادبیات فارسی است.
می‌توانی شعر معرفی کنی، تحلیل کنی، معنی کنی و با لحن گرم و ادبی جواب بدهی.
"""

@app.route("/", methods=["GET"])
def home():
    return "Zahra Agent Backend is Running!"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "لطفاً پیامی بنویسید."})

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"reply": "خطا: کلید API تنظیم نشده."})

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://zahrajafarian.freepage.cc",
            "X-Title": "Zahra Jafarian Agent"
        }

        payload = {
            "model": "openrouter/free",   # مدل رایگان و خوب
            "messages": [
                {"role": "system", "content": SITE_KNOWLEDGE},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }

        response = requests.post(url, json=payload, headers=headers, timeout=40)
        result = response.json()

        if "error" in result:
            return jsonify({"reply": f"خطا: {result['error'].get('message', str(result['error']))}"})

        bot_reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"reply": f"خطای سرور: {str(e)}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
