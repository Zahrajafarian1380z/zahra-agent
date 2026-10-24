from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

# تنظیم کلید API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# استفاده از نسخه به روز و رسمی مدل جمنای
model = genai.GenerativeModel("gemini-2.5-flash")


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
    # چاپ خطا در لوگ‌های رندر جهت دیباگ آسان
    print("Error details:", str(e))
    return jsonify({
        "reply": "خطایی رخ داد، لطفاً دوباره تلاش کنید.",
        "error_details": str(e),
    })


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
