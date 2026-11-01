import os
import json
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# دریافت اطلاعات اتصال به Supabase از متغیرهای محیطی Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

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

# ====================== ذخیره چت‌ها در Supabase ======================
def save_chat_log(user_msg, bot_reply):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase credentials not set!")
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/chat_logs"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        payload = {
            "user_msg": user_msg,
            "bot_reply": bot_reply
        }
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print("Error saving to Supabase:", e)

# ====================== جستجوی پیشرفته در اشعار ======================
def search_poems(query, top_k=4):
    if not query or not POEMS:
        return []

    query = query.lower().strip()
    search_terms = set(re.findall(r"\w+", query))
    
    scored = []
    for poem in POEMS:
        score = 0
        title = poem.get("title", "").lower()
        text = poem.get("text", "").lower()
        category = poem.get("category", "").lower()
        tags = " ".join(poem.get("tags", [])).lower()

        for term in search_terms:
            if len(term) < 2:
                continue
            if term in title: score += 15
            if term in text: score += 5
            if term in category: score += 8
            if term in tags: score += 10

        if query in title: score += 30
        if query in text: score += 15

        if score > 0:
            scored.append((score, poem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]

# ====================== پرامپت هوشمند و پیشنهاددهنده ======================
BASE_PROMPT = """
تو «دستیار آنلاین ادبی» و اختصاصی سایت زهرا جعفریان هستی.
لحن‌ات گرم، شاعرانه، ادبی، صمیمی و پیشنهاددهنده است.

قوانین بسیار مهم رفتاری:
1. تمرکز اصلی و اولویت اول تو، جستجو و پاسخگویی بر اساس «شعرهای مرتبط پیدا شده» از دیتابیس سایت است. اگر شعری مرتبط پیدا شد، حتماً متن، عنوان و لینک آن را به کاربر معرفی کن.
2. اگر کاربر درباره موضوعی پرسید که مستقیماً در دیتابیس شعر و ترانه‌های سایت نبود، هرگز به او نگگو «اطلاعاتی ندارم» یا «نمی‌توانم جواب دهم». بلکه با همان لحن گرم و شاعرانه‌ات دوستانه به او پاسخ بده و در ابتدا یا انتهای سخنت به نرمی اشاره کن که این پرسش خارج از آرشیو تخصصی اشعار سایت است، اما با این حال با کمال میل به او پاسخ می‌دهی.
3. هرگز و تحت هیچ شرایطی از علامت‌های مارکدان مانند ** یا __ استفاده نکن. متن باید کاملاً ساده باشد.
4. عنوان شعر را ساده و بدون ستاره بنویس.
5. لینک مطالعه در سایت را دقیقاً به شکل زیر قرار بده:
🔗 [مطالعه در سایت](لینک کامل)
6. در انتهای هر پاسخ، خط منبع را دقیقاً به شکل زیر بنویس:
منبع: زهرا جعفریان | zahrajafarian.freepage.cc
7. در انتهای پاسخ‌هایت، حتماً با یک سوال گرم یا پیشنهاد مرتبط، مخاطب را به گفتگوی بیشتر دعوت کن.
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
            return jsonify({"reply": "سلام به آرشیو شعر و ترانه خوش آمدید! من دستیار آنلاین ادبی هستم. دوست داری چه موضوع یا شعری را با هم مرور کنیم؟"})

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"reply": "خطا: کلید API تنظیم نشده است."})

        relevant_poems = search_poems(user_message, top_k=3)

        context = ""
        if relevant_poems:
            context = "\n\n=== شعرهای مرتبط پیدا شده از سایت ===\n"
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
            context = "\n\n=== هیچ شعر مرتبطی در دیتابیس سایت پیدا نشد. ===\n"

        system_content = BASE_PROMPT + context

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
            "temperature": 0.6,
            "max_tokens": 1200
        }

        response = requests.post(url, json=payload, headers=headers, timeout=45)
        result = response.json()

        if "error" in result:
            return jsonify({"reply": f"خطا: {result['error'].get('message', str(result['error']))}"})

        bot_reply = result["choices"][0]["message"]["content"]
        bot_reply = bot_reply.replace("**", "").replace("__", "")

        # ذخیره امن در دیتابیس ابری Supabase
        save_chat_log(user_message, bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"reply": f"خطای سرور: {str(e)}"})

# مسیر برای خواندن تاریخچه چت‌ها از Supabase
@app.route("/logs", methods=["GET"])
def view_logs():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "Supabase not configured"})
    try:
        url = f"{SUPABASE_URL}/rest/v1/chat_logs?select=*&order=created_at.desc"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        res = requests.get(url, headers=headers)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
