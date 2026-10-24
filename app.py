import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)


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

    api_key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": user_message}]}]}

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    bot_reply = (
        result.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "متوجه نشدم، لطفاً دوباره بگو.")
    )

    return jsonify({"reply": bot_reply})
  except Exception as e:
    print("Error:", str(e))
    return jsonify({"reply": "خطایی رخ داد، لطفاً دوباره تلاش کنید."})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
