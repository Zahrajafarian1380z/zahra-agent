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
            "user_msg": str(user_msg or ""),
            "bot_reply": str(bot_reply or "")
        }
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print("Error saving to Supabase:", e)

def search_poems(query, top_k=4):
    if not query or not POEMS:
        return []

    query = str(query).lower().strip()
    search_terms = set(re.findall(r"\w+", query))
    
    scored = []
    for poem in POEMS:
        score = 0
        title = str(poem.get("title", "") or "").lower()
        text = str(poem.get("text", "") or "").lower()
        category = str(poem.get("category", "") or "").lower()
        tags_list = poem.get("tags", []) or []
        tags = " ".join([str(t) for t in tags_list]).lower()

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
1. اولویت اول تو، شعرهای مرتبط پیدا شده از دیتابیس است. اگر شعر مرتبطی بود، متن آن را به دلنشین‌ترین شکل بفرست.
2. اگر موضوعی خارج از دیتابیس بود یا کاربر حرف دیگری زد، ربات نباید خشک برخورد کند؛ با کمال میل و صمیمیت پاسخ بده و بگو که گرچه این موضوع در آرشیو اشعار مستقیم نیست، اما با دل و جان همراهش هستی.
3. ممنوعیت مطلق مارکدان و هشتگ: تحت هیچ شرایطی از علامت‌های ستاره (**)، هشتگ (## یا #) یا کاراکترهای مارکدان استفاده نکن. متن باید کاملاً ساده، پاک و روان باشد.
4. لینک مطالعه در سایت را فقط و فقط به شکل دقیق زیر بنویس و هیچ کلمه‌ی انگلیسی یا اضافه‌ای داخل کروشه نگذار:
🔗 [مطالعه در سایت](لینک کامل شعر)
5. در انتهای هر پاسخ، خط منبع را دقیقاً به شکل زیر بنویس:
منبع: زهرا جعفریان | zahrajafarian.freepage.cc
6. بخش پیشنهادات تعاملی و پویا: در انتهای پاسخ خود، متناسب با حال و هوای پیام کاربر و شعر ارائه شده، یک پیشنهاد یا سوال جذاب و خلاقانه مطرح کن (مثلاً بپرس: «ترانه عاشقانه دوست داری یا غمگین؟» یا «دوست داری بیتی درباره‌ی باران یا تنهایی با هم مرور کنیم؟»). این پیشنهاد نباید یک جمله کلیشه و تکراری باشد، بلکه باید کاملاً بر اساس صحبت‌های لحظه‌ای کاربر شکل بگیرد.
"""

@app.route("/", methods=["GET"])
def home():
    return f"Zahra Agent Backend is Running! | {len(POEMS)} poems loaded"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        user_message = str(data.get("message", "")).strip()

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
                p_title = str(p.get('title', 'بدون عنوان') or 'بدون عنوان')
                p_cat = str(p.get('category', 'نامشخص') or 'نامشخص')
                p_link = str(p.get('link', 'https://zahrajafarian.freepage.cc') or 'https://zahrajafarian.freepage.cc')
                p_text = str(p.get('text', '') or '')
                context += f"""
شعر {i}:
عنوان: {p_title}
دسته‌بندی: {p_cat}
لینک: {p_link}
متن کامل:
{p_text}
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
            err_msg = result['error'].get('message', str(result['error']))
            return jsonify({"reply": f"خطا در ارتباط با هوش مصنوعی: {err_msg}"})

        choices = result.get("choices", [])
        if not choices:
            return jsonify({"reply": "پاسخی از مدل دریافت نشد."})

        bot_reply = choices[0].get("message", {}).get("content", "")
        bot_reply = str(bot_reply or "")
        
        # پاکسازی هشتگ‌ها و کاراکترهای اضافی
        bot_reply = re.sub(r'#+\s*', '', bot_reply)
        bot_reply = bot_reply.replace("**", "").replace("__", "").replace("##", "")

        # اصلاح خودکار لینک‌های احتمالی معیوب مدل هوش مصنوعی
        bot_reply = re.sub(r'\[.*?\]\((https?:\/\/[^\s)]+)\)', r'[مطالعه در سایت](\1)', bot_reply)

        save_chat_log(user_message, bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error in /chat route:", str(e))
        return jsonify({"reply": "خطای سرور رخ داد. لطفاً چند لحظه دیگر دوباره تلاش کنید."})

@app.route("/logs", methods=["GET"])
def view_logs_route():
    # کد مربوط به نمایش لاگ‌ها در صورت نیاز
    pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
            "user_msg": str(user_msg or ""),
            "bot_reply": str(bot_reply or "")
        }
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print("Error saving to Supabase:", e)

def search_poems(query, top_k=4):
    if not query or not POEMS:
        return []

    query = str(query).lower().strip()
    search_terms = set(re.findall(r"\w+", query))
    
    scored = []
    for poem in POEMS:
        score = 0
        title = str(poem.get("title", "") or "").lower()
        text = str(poem.get("text", "") or "").lower()
        category = str(poem.get("category", "") or "").lower()
        tags_list = poem.get("tags", []) or []
        tags = " ".join([str(t) for t in tags_list]).lower()

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
1. اولویت اول تو، شعرهای مرتبط پیدا شده از دیتابیس است. اگر شعر مرتبطی بود، متن آن را به دلنشین‌ترین شکل بفرست.
2. اگر موضوعی خارج از دیتابیس بود یا کاربر حرف دیگری زد، ربات نباید خشک برخورد کند؛ با کمال میل و صمیمیت پاسخ بده و بگو که گرچه این موضوع در آرشیو اشعار مستقیم نیست، اما با دل و جان همراهش هستی.
3. ممنوعیت مطلق مارکدان و هشتگ: تحت هیچ شرایطی از علامت‌های ستاره (**)، هشتگ (## یا #) یا کاراکترهای مارکدان استفاده نکن. متن باید کاملاً ساده، پاک و روان باشد.
4. لینک مطالعه در سایت را فقط و فقط به شکل دقیق زیر بنویس و هیچ کلمه‌ی انگلیسی یا اضافه‌ای داخل کروشه نگذار:
🔗 [مطالعه در سایت](لینک کامل شعر)
5. در انتهای هر پاسخ، خط منبع را دقیقاً به شکل زیر بنویس:
منبع: زهرا جعفریان | zahrajafarian.freepage.cc
6. در انتهای پاسخ، با توجه به صحبت کاربر، یک سوال یا پیشنهاد کاملاً مرتبط برای ادامه گفتگو مطرح کن.
"""

@app.route("/", methods=["GET"])
def home():
    return f"Zahra Agent Backend is Running! | {len(POEMS)} poems loaded"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        user_message = str(data.get("message", "")).strip()

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
                p_title = str(p.get('title', 'بدون عنوان') or 'بدون عنوان')
                p_cat = str(p.get('category', 'نامشخص') or 'نامشخص')
                p_link = str(p.get('link', 'https://zahrajafarian.freepage.cc') or 'https://zahrajafarian.freepage.cc')
                p_text = str(p.get('text', '') or '')
                context += f"""
شعر {i}:
عنوان: {p_title}
دسته‌بندی: {p_cat}
لینک: {p_link}
متن کامل:
{p_text}
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
            err_msg = result['error'].get('message', str(result['error']))
            return jsonify({"reply": f"خطا در ارتباط با هوش مصنوعی: {err_msg}"})

        choices = result.get("choices", [])
        if not choices:
            return jsonify({"reply": "پاسخی از مدل دریافت نشد."})

        bot_reply = choices[0].get("message", {}).get("content", "")
        bot_reply = str(bot_reply or "")
        
        # پاکسازی هشتگ‌ها و کاراکترهای اضافی
        bot_reply = re.sub(r'#+\s*', '', bot_reply)
        bot_reply = bot_reply.replace("**", "").replace("__", "").replace("##", "")

        # اصلاح خودکار لینک‌های احتمالی معیوب مدل هوش مصنوعی
        bot_reply = re.sub(r'\[.*?\]\((https?:\/\/[^\s)]+)\)', r'[مطالعه در سایت](\1)', bot_reply)

        save_chat_log(user_message, bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error in /chat route:", str(e))
        return jsonify({"reply": "خطای سرور رخ داد. لطفاً چند لحظه دیگر دوباره تلاش کنید."})

@app.route("/logs", methods=["GET"])
def view_logs():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return "Supabase not configured", 500
    try:
        url = f"{SUPABASE_URL}/rest/v1/chat_logs?select=*&order=created_at.desc"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        res = requests.get(url, headers=headers)
        logs = res.json() if res.status_code == 200 else []
        
        html = """
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>تاریخچه گفتگوهای دستیار ادبی</title>
            <style>
                body { font-family: Tahoma, sans-serif; background: #fff9fa; color: #333; padding: 20px; direction: rtl; }
                h1 { color: #8B0000; text-align: center; font-size: 22px; margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
                th, td { padding: 12px 15px; border-bottom: 1px solid #ffe0e5; text-align: right; font-size: 13.5px; line-height: 1.8; }
                th { background: #8B0000; color: #fff; font-size: 14px; }
                tr:hover { background: #fff0f3; }
                .time { color: #666; font-size: 11.5px; white-space: nowrap; }
                .user-box { font-weight: bold; color: #8B0000; }
                .bot-box { color: #222; }
            </style>
        </head>
        <body>
            <h1>📜 تاریخچه گفتگوهای دستیار آنلاین ادبی (زهرا جعفریان)</h1>
            <table>
                <tr>
                    <th style="width: 15%;">زمان ثبت</th>
                    <th style="width: 35%;">پیام کاربر</th>
                    <th style="width: 50%;">پاسخ ربات</th>
                </tr>
        """
        for log in logs:
            time_str = str(log.get('created_at', ''))
            user_msg = str(log.get('user_msg', ''))
            bot_reply = str(log.get('bot_reply', '')).replace('\n', '<br>')
            html += f"""
                <tr>
                    <td class="time">{time_str}</td>
                    <td class="user-box">{user_msg}</td>
                    <td class="bot-box">{bot_reply}</td>
                </tr>
            """
        html += """
            </table>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"Error loading logs: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
