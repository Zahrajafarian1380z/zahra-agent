from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# گرفتن کلید API از تنظیمات امنیتی سرور
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/chat", methods=["POST"])
def chat():
  try:
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
      return jsonify({"reply": "لطفاً پیامی بنویسید."})

    response = model.generate_content(user_message)
    return jsonify({"reply": response.text})
  except Exception as e:
    return jsonify({"reply": "خطایی رخ داد، لطفاً دوباره تلاش کنید."})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
