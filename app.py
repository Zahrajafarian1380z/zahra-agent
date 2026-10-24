import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# === دانش سایت رو اینجا بذار (بعداً می‌تونی از فایل یا دیتابیس بخونی) ===
SITE_KNOWLEDGE = """
تو دستیار هوشمند سایت هستی.
سایت درباره شعر و ادبیات فارسیه.
می‌تونی شعر معرفی کنی، تحلیل کنی، معنی کنی، سبک شعرا رو توضیح بدی و به سوالات کاربران جواب بدی.

اطلاعات مهم سایت:
- [اینجا درباره سایت، شعرای معروفی که داری، دسته‌بندی‌ها، قوانین و ... بنویس]
- مثلاً: ما شعرهای کلاسیک و معاصر داریم، تحلیل ادبی می‌کنیم و ...
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

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"reply": "خطا: کلید API تنظیم نشده. لطفاً متغیر محیطی GEMINI_API_KEY را چک کنید."})

        # مدل به‌روز (می‌تونی gemini-3.8-flash یا gemini-3.5-flash-lite هم بذاری)
        model = "gemini-2.5-flash"   # یا gemini-3.8-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_message}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SITE_KNOWLEDGE}]
            },
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()

        # اگر ارور از گوگل اومد، دقیق نشون بده
        if "error" in result:
            error_msg = result["error"].get("message", "نامشخص")
            error_code = result["error"].get("code", "")
            print(f"Gemini Error [{error_code}]: {error_msg}")  # توی لاگ Render می‌بینی
            return jsonify({"reply": f"خطای گوگل ({error_code}): {error_msg}"})

        # استخراج جواب
        try:
            bot_reply = result["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"reply": bot_reply})
        except (KeyError, IndexError, TypeError):
            print("Unexpected response:", result)
            return jsonify({"reply": "پاسخی از مدل دریافت نشد."})

    except Exception as e:
        print("Server Error:", str(e))
        return jsonify({"reply": f"خطای سرور: {str(e)}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
