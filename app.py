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
    # استفاده از مدل استاندارد و نسخه سازگار API
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": user_message}]}]}

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    # استخراج امن پاسخ از گوگل
    if "candidates" in result and len(result["candidates"]) > 0:
      candidate = result["candidates"][0]
      if (
          "content" in candidate
          and "parts" in candidate["content"]
          and len(candidate["content"]["parts"]) > 0
      ):
        bot_reply = candidate["content"]["parts"][0].get("text", "")
        if bot_reply:
          return jsonify({"reply": bot_reply})

    if "error" in result:
      return jsonify(
          {"reply": f"خطای گوگل: {result['error'].get('message', 'نامشخص')}"}
      )

    return jsonify({"reply": "پاسخی از مدل دریافت نشد."})
  except Exception as e:
    print("Error:", str(e))
    return jsonify({"reply": f"خطای سرور: {str(e)}"})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
