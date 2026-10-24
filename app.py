import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# تنظیم کلید API با استفاده از کتابخانه رسمی گوگل
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)


@app.route("/", methods=["GET"])
def home():
  return "Zahra Agent Backend is Running!"


@app.route("/chat", methods=["POST"])
def chat():
  try:
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
      return jsonify({"reply": "لطفاً پیامی بنویسید."})

    # استفاده از مدل gemini-pro که پایداری صددرصدی روی تمام کلیدها دارد
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(user_message)

    return jsonify({"reply": response.text})
  except Exception as e:
    print("Error details:", str(e))
    return jsonify({"reply": f"خطا در پردازش پاسخ: {str(e)}"})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
