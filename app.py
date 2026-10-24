import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)


@app.route("/chat", methods=["POST"])
def chat():
  try:
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
      return jsonify({"reply": "لطفاً پیامی بنویسید."})

    # استفاده از مدل استاندارد فلش
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(user_message)
    return jsonify({"reply": response.text})
  except Exception as e:
    print(f"Error: {e}")
    return jsonify({"reply": "خطایی رخ داد، لطفاً دوباره تلاش کنید."})


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
