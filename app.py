import os
import json
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def load_poems():
    try:
        with open("poems.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading poems.json:", e)
        return []

POEMS = load_poems()
print(f"✅ {len(POEMS)} شعر بارگذاری شد.")

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
        res = requests.post(url, json=payload, headers=headers, timeout=5)
        print("Supabase save response:", res.status_code)
    except Exception as e:
        print("Error saving to Supabase:", e)

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

BASE_PROMPT = """
تو «دستیار آنلاین ادبی» و صمیمیِ سایت زهرا جعفریان هستی. مثل یک انسان واقعی، با احساس، گرم و باهوش با مخاطب گفتگو کن.

قوانین سخت‌گیرانه و حیاتی:
1. اولویت اول تو، شعرهای مرتبط پیدا شده از دیتابیس است. اگر شعر مرتبطی بود، با مهربانی آن را معرفی کن.
2. اگر موضوعی خارج از دیتابیس بود یا کاربر حرف دیگری زد، ربات نباید خشک یا رباتیک برخورد کند؛ بلکه با کمال میل، صمیمیت و به زیبایی به او پاسخ بده و بگو که گرچه این موضوع در آرشیو اشعار نیست، اما با دل و جان همراهش هستی.
3. ممنوعیت مطلق مارکدان: تحت هیچ شرایطی از علامت‌های ستاره (**)، هشتگ‌های اضافی (##)، خطوط تیره دوتایی یا فرمت‌های زشت مارکدان در متن استفاده نکن. متن باید کاملاً تمیز، ساده و بدون کاراکترهای اضافی باشد.
4. عنوان شعر را کاملاً ساده و معمولی (بدون هیچ علامت یا ستاره‌ای) بنویس.
5. لینک مطالعه در سایت را فقط و فقط به شکل دقیق زیر بنویس و به هیچ وجه کلمه انگلیسی یا کلمه دیگری داخل کروشه نگذار:
🔗 [مطالعه در سایت](لینک کامل شعر))
6. در انتهای هر پاسخ، خط منبع را دقیقاً به شکل زیر بنویس:
منبع: زهرا جعفریان | zahrajafarian.freepage.cc
7. در انتهای پاسخ، با توجه به صحبت کاربر، یک سوال یا پیشنهاد کاملاً مرتبط برای ادامه گفتگو مطرح کن.
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
            return jsonify({"reply": "سلام! من دستیار آنلاین ادبی هستم. خوشحالم که اینجا هستی. دوست داری درباره چه شعر یا موضوعی با هم گپ بزنیم؟"})

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
            context = "\n\n=== هیچ شعر مستقیمی در دیتابیس پیدا نشد، با لحن انسانی و صمیمی پاسخ بده. ===\n"

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
            "temperature": 0.7,
            "max_tokens": 1200
        }

        response = requests.post(url, json=payload, headers=headers, timeout=45)
        result = response.json()

        if "error" in result:
            return jsonify({"reply": f"خطا: {result['error'].get('message', str(result['error']))}"})

        bot_reply = result["choices"][0]["message"]["content"]
        
        # پاکسازی کامل تمام هشتگ‌ها و ستاره‌های اضافی از خروجی ربات
        bot_reply = re.sub(r'#+\s*', '', bot_reply)
        bot_reply = bot_reply.replace("**", "").replace("__", "").replace("##", "")

        save_chat_log(user_message, bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"reply": f"خطای سرور: {str(e)}"})

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
