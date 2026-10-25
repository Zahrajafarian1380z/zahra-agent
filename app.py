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
def search_poems(query, top_k=5):
    if not query or not POEMS:
        return []

    query = query.lower().strip()

    # دیکشنری کلمات مشابه (می‌تونی هر چقدر خواستی اضافه کنی)
    synonyms = {
        "بارون": ["باران", "بارانی", "بارندگی", "نم‌نم", "نم نم"],
        "باران": ["بارون", "بارانی", "بارندگی"],
        "عاشقانه": ["عشق", "عاشق", "دلبر", "معشوق", "عاشقی"],
        "عشق": ["عاشقانه", "عاشق", "دلبر"],
        "غمگین": ["غم", "اندوه", "حزن", "دلتنگ", "دلگیر"],
        "غم": ["غمگین", "اندوه", "حزن"],
        "شاد": ["شادی", "خوشحالی", "سرور", "بهشتی"],
        "شادی": ["شاد", "خوشحالی"],
        "پاییز": ["خزان", "پاییزی"],
        "بهار": ["بهاری", "نوروز", "اردیبهشت", "فروردین"],
        "زمستان": ["زمستونی", "برف", "سرد"],
        "شب": ["شبی", "شبانه"],
        "دل": ["قلب", "سینه"],
    }

    # کلمات اصلی جستجو + مترادف‌ها
    search_terms = set(re.findall(r"\w+", query))
    expanded_terms = set(search_terms)

    for word in list(search_terms):
        if word in synonyms:
            expanded_terms.update(synonyms[word])
        # اضافه کردن خود کلمه بدون پسوندهای رایج
        for suffix in ["ی", "انه", "ین", "ون"]:
            if word.endswith(suffix) and len(word) > 3:
                expanded_terms.add(word[:-len(suffix)])

    scored = []

    for poem in POEMS:
        score = 0
        title = poem.get("title", "").lower()
        text = poem.get("text", "").lower()
        category = poem.get("category", "").lower()
        tags = " ".join(poem.get("tags", [])).lower()
        full_content = f"{title} {text} {category} {tags}"

        # امتیاز برای هر کلمه
        for term in expanded_terms:
            if len(term) < 2:
                continue

            if term in title:
                score += 12
            if term in text:
                score += 5
            if term in category:
                score += 6
            if term in tags:
                score += 7

            # اگر کلمه کامل داخل متن باشه امتیاز بیشتر
            if f" {term} " in f" {text} ":
                score += 3

        # اگر کل عبارت جستجو داخل عنوان باشه امتیاز خیلی بالا
        if query in title:
            score += 20
        if query in text:
            score += 10

        if score > 0:
            scored.append((score, poem))

    # مرتب‌سازی و برگرداندن بهترین‌ها
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]

# ====================== System Prompt ======================
BASE_PROMPT = """
تو دستیار هوشمند رسمی سایت زهرا جعفریان هستی.
لحن‌ات همیشه گرم، ادبی، صمیمی و محترمانه است.

قوانین خیلی مهم برای فرمت پاسخ:

1. وقتی شعر می‌دی، دقیقاً به این شکل بنویس:

**عنوان شعر**

متن کامل شعر
(هر خط در یک خط جدا)

🔗 [مطالعه در سایت](لینک کامل و صحیح)

---

2. لینک را حتماً به صورت Markdown بنویس تا آبی و قابل کلیک شود.
3. هیچ‌وقت از ** ستاره زیاد یا فرمت‌های عجیب استفاده نکن.
4. اگر چند شعر می‌دی، بین آن‌ها خط جداکننده `---` بگذار.
5. در پایان اگر خواستی تحلیل کوتاه و زیبایی اضافه کن.
6. لینک را کامل و صحیح بنویس (هیچ کاراکتر اضافی مثل ] یا [ نگذار).

مثال خوب:

**خفته نباشی...**

وقت است درخشان شوی و خفته نباشی
بیهوده پی غصه ی پیوسته نباشی
...

🔗 [مطالعه در سایت](https://zahrajafarian.freepage.cc/f-1405/)

---
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
