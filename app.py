import os
import json
import re
from datetime import datetime
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

# ====================== ذخیره تاریخچه چت‌ها ======================
def save_chat_log(user_msg, bot_reply):
    try:
        log_file = "chat_history.json"
        history = []
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        
        history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_msg,
            "bot": bot_reply
        })
        
        # نگهداری ۲۰۰ پیام آخر برای جلوگیری از حجیم شدن فایل
        if len(history) > 200:
            history = history[-200:]
            
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving chat log:", e)

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
            if term in title:
                score += 15
            if term in text:
                score += 5
            if term in category:
                score += 8
            if term in tags:
                score += 10

        if query in title:
            score += 30
        if query in text:
            score += 15

        if score > 0:
            scored.append((score, poem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]

# ====================== پرامپت سیستم سخت‌گیرانه ======================
BASE_PROMPT = """
تو دستیار هوشمند و اختصاصی سایت زهرا جعفریان هستی.
لحن‌ات گرم، شاعرانه، ادبی و صمیمی است.

قوانین بسیار مهم:
1. اولویت اول و مطلق تو، پاسخ دادن بر اساس «شعرهای مرتبط پیدا شده» از دیتابیس سایت است.
2. هرگز و تحت هیچ شرایطی از علامت‌های مارکدان مانند ** یا __ برای ضخیم کردن متن استفاده نکن. متن باید کاملاً ساده و تمیز باشد.
3. عنوان شعر را ساده و بدون ستاره بنویس.
4. لینک را دقیقاً به شکل زیر و به صورت استاندارد قرار بده تا در فرانت‌اند قابل کلیک باشد:
🔗 [مطالعه در سایت](لینک کامل)
5. اگر کاربر سوالی پرسید یا درخواستی داد که هیچ ارتباطی با شعرهای سایت نداشت و در بخش «شعرهای مرتبط» چیزی پیدا نشد، صراحتاً و با لحنی محترمانه به او بگو:
«این مطلب در حال حاضر در آرشیو و مطالب سایت زهرا جعفریان وجود ندارد، اما...» (سپس پاسخی کوتاه بده یا راهنمایی‌اش کن که درباره اشعار سایت بپرسد).
6. در پایان هر پاسخ دقیقاً این خط را قرار بده:
منبع: زهرا جعفریان | https://zahrajafarian.freepage.cc/
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
            return jsonify({"reply": "خطا: کلید API تنظیم نشده است."})

        # جستجوی اشعار مرتبط
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
            "temperature": 0.5,
            "max_tokens": 1200
        }

        response = requests.post(url, json=payload, headers=headers, timeout=45)
        result = response.json()

        if "error" in result:
            return jsonify({"reply": f"خطا: {result['error'].get('message', str(result['error']))}"})

        bot_reply = result["choices"][0]["message"]["content"]
        
        # پاکسازی نهایی برای اطمینان از حذف ستاره‌های ناخواسته احتمالی
        bot_reply = bot_reply.replace("**", "").replace("__", "")

        # ذخیره تاریخچه گفتگو
        save_chat_log(user_message, bot_reply)

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"reply": f"خطای سرور: {str(e)}"})

# مسیر جدید برای خواندن تاریخچه چت‌ها توسط شما
@app.route("/logs", methods=["GET"])
def view_logs():
    log_file = "chat_history.json"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                return jsonify(json.load(f))
            except:
                return jsonify([])
    return jsonify([])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0",port=port)
