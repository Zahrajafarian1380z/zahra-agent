import os
import json
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ====================== بارگذاری اشعار ======================
def load_poems():
    try:
        with open("poems.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading poems.json:", e)
        return []

POEMS = load_poems()
print(f"✅ {len(POEMS)} شعر بارگذاری شد.")

# ====================== جستجوی ساده ======================
def search_poems(query, top_k=4):
    if not query or not POEMS:
        return []

    query = query.lower().strip()
    scored = []

    for poem in POEMS:
        score = 0
        title = poem.get("title", "").lower()
        text = poem.get("text", "").lower()
        category = poem.get("category", "").lower()
        tags = " ".join(poem.get("tags", [])).lower()

        # امتیازدهی
        if query in title:
            score += 10
        if query in text:
            score += 6
        if query in category:
            score += 4
        if query in tags:
            score += 5

        # کلمات کلیدی جداگانه
        words = re.findall(r"\w+", query)
        for word in words:
            if len(word) < 2:
                continue
            if word in title:
                score += 3
            if word in text:
                score += 1.5
            if word in tags:
                score += 2

        if score > 0:
            scored.append((score, poem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]

# ====================== System Prompt ======================
BASE_PROMPT = """
تو دستیار هوشمند رسمی سایت زهرا جعفریان هستی.
لحن‌ات همیشه گرم، ادبی، صمیمی و محترمانه است.

قوانین مهم:
- وقتی شعری مرتبط پیدا شد، حتماً متن کامل شعر را بنویس.
- بعد از متن شعر، لینک صفحه را هم بده.
- اگر کاربر خواست، تحلیل کوتاه و زیبایی از شعر ارائه بده.
- اگر چند شعر مرتبط بود، ۲ تا ۳ تا از بهترین‌ها را نشان بده.
- اگر شعری پیدا نشد، مؤدبانه بگو و پیشنهاد بده که در سایت جستجو کند.
- کپی اشعار فقط با ذکر منبع و لینک مجاز است.
"""

@app.route("/", methods=["GET"])
def home():
    return f"Zahra Agent Backend is Running! | {len(POEMS)} poems loaded"

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

        # جستجوی شعرهای مرتبط
        relevant_poems = search_poems(user_message, top_k=4)

        # ساخت context از شعرها
        context = ""
        if relevant_poems:
            context = "\n\n=== شعرهای مرتبط پیدا شده ===\n"
            for i, p in enumerate(relevant_poems, 1):
                context += f"""
شعر {i}:
عنوان: {p.get('title')}
دسته‌بندی: {p.get('category', 'نامشخص')}
لینک: {p.get('link')}
متن کامل:
{p.get('text')}
----------------------------
"""
        else:
            context = "\n\nهیچ شعر مرتبطی پیدا نشد."

        system_content = BASE_PROMPT + context

        # درخواست به OpenRouter
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://zahrajafarian.freepage.cc",
            "X-Title": "Zahra Jafarian Agent"
        }

        payload = {
            "model": "openrouter/free",
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }

        response = requests.post(url, json=payload, headers=headers, timeout=45)
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
