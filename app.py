# =====================================================================
# سامانه پژوهشی سبک‌شناسی شعر فارسی
# TF-IDF + Logistic Regression (۵ کلاس) + رفع ابهام تعاملی + لاگ استاندارد
# نسخه اصلاح‌شده برای استفاده در پایان‌نامه
# =====================================================================
import os
import datetime
import glob
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

LOG_FILENAME = 'style_evaluation_thesis_log.csv'

# ---------------------------------------------------------------------
# ۱. بارگذاری و پاک‌سازی داده‌ها
# ---------------------------------------------------------------------
print("📂 در حال بارگذاری فایل اکسل...")
file_name = '/content/poetry_dataset_scored_final.xlsx'

if not os.path.exists(file_name):
    found = glob.glob('*poetry_dataset*.xlsx')
    if found:
        file_name = found[0]
    else:
        raise FileNotFoundError("فایل اکسل پیدا نشد. نام فایل را بررسی کنید.")

df_raw = pd.read_excel(file_name)

required_cols = ['poem_id', 'poet_name', 'style', 'category', 'raw_poem_text']
missing = [c for c in required_cols if c not in df_raw.columns]
if missing:
    raise ValueError(f"ستون‌های ضروری موجود نیستند: {missing}")

df_poems = (
    df_raw[required_cols]
    .drop_duplicates(subset=['poem_id'])
    .dropna(subset=['style', 'raw_poem_text'])
    .reset_index(drop=True)
)

print(f"✅ تعداد اشعار یکتا پس از پاک‌سازی: {len(df_poems)}")
print("📊 توزیع کلاس‌ها:\n", df_poems['style'].value_counts())
print()

# بررسی سازگاری نام کلاس‌ها با نگاشت کاربر
EXPECTED_CLASSES = {'Khorasani', 'Iraqi', 'Indian', 'Literary_Return', 'Contemporary'}
actual_classes = set(df_poems['style'].unique())
if not actual_classes.issubset(EXPECTED_CLASSES):
    print("⚠️ هشدار: نام برخی کلاس‌ها با نگاشت کاربر هم‌خوان نیست.")
    print("   کلاس‌های موجود در دیتاست:", sorted(actual_classes))
    print("   کلاس‌های مورد انتظار:", sorted(EXPECTED_CLASSES))
    print("   نگاشت پاسخ کاربر ممکن است برچسبی تولید کند که مدل هرگز ندیده است.\n")

# ---------------------------------------------------------------------
# ۲. آماده‌سازی برچسب‌ها و تقسیم آموزش/آزمون
# ---------------------------------------------------------------------
X_text = df_poems['raw_poem_text']
y_labels = df_poems['style']

le = LabelEncoder()
y_encoded = le.fit_transform(y_labels)

print("نگاشت LabelEncoder:")
for i, name in enumerate(le.classes_):
    print(f"  {i} → {name}")
print()

X_train_txt, X_test_txt, y_train, y_test = train_test_split(
    X_text, y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

# ---------------------------------------------------------------------
# ۳. TF-IDF و آموزش مدل
# ---------------------------------------------------------------------
vectorizer = TfidfVectorizer(
    max_features=15000,
    ngram_range=(1, 2),
    min_df=2
)

X_train_vec = vectorizer.fit_transform(X_train_txt)
X_test_vec  = vectorizer.transform(X_test_txt)

print("🚀 آموزش Logistic Regression ...")
clf_model = LogisticRegression(
    C=2.0,
    max_iter=1000,
    class_weight='balanced',
    random_state=42
)
clf_model.fit(X_train_vec, y_train)
print("✨ آموزش تمام شد.\n")

# ---------------------------------------------------------------------
# ۴. ارزیابی مدل روی مجموعه آزمون (گام ضروری برای پایان‌نامه)
# ---------------------------------------------------------------------
y_pred = clf_model.predict(X_test_vec)

acc = accuracy_score(y_test, y_pred)
macro_f1 = f1_score(y_test, y_pred, average='macro')
weighted_f1 = f1_score(y_test, y_pred, average='weighted')

print("=" * 65)
print("📈 نتایج ارزیابی مدل روی مجموعه آزمون (۲۰٪ داده‌ها)")
print("=" * 65)
print(f"Accuracy          : {acc:.4f}")
print(f"Macro-F1          : {macro_f1:.4f}")
print(f"Weighted-F1       : {weighted_f1:.4f}")
print()
print("گزارش تفصیلی (Precision / Recall / F1 برای هر کلاس):")
print(classification_report(
    y_test, y_pred,
    target_names=le.classes_,
    digits=4
))
print("ماتریس درهم‌ریختگی (ردیف = واقعی، ستون = پیش‌بینی):")
print(pd.DataFrame(
    confusion_matrix(y_test, y_pred),
    index=le.classes_,
    columns=le.classes_
))
print("=" * 65)
print()

# یادداشت روش‌شناختی برای پایان‌نامه:
# تقسیم تصادفی (stratified) انجام شده است. اگر هدف تعمیم به شاعران دیده‌نشده باشد،
# بهتر است تقسیم در سطح شاعر (GroupKFold یا train_test_split بر اساس poet_name) انجام شود.
# در وضعیت فعلی، شعرهای یک شاعر ممکن است هم در آموزش و هم در آزمون باشند.

# ---------------------------------------------------------------------
# ۵. تابع لاگ استاندارد پژوهشی
# ---------------------------------------------------------------------
def log_thesis_evaluation(
    poem_text,
    true_label,
    top_1, prob_1,
    top_2, prob_2,
    was_ambiguous,
    user_choice,
    final_resolved
):
    """
    ثبت یک ردیف ارزیابی با تفکیک کامل متغیرها.
    - matched_model_and_user فقط وقتی کاربر واقعاً پاسخ معتبر داده محاسبه می‌شود.
    - صحت مدل و صحت نتیجه نهایی نسبت به برچسب مرجع در ستون‌های جداگانه ذخیره می‌شود.
    """
    # توافق مدل و کاربر
    if user_choice not in (None, 'None', ''):
        matched = (top_1 == user_choice)
    else:
        matched = None   # هیچ توافقی اندازه‌گیری نشده

    # صحت نسبت به برچسب مرجع (اگر مشخص باشد)
    if true_label and true_label != 'Unknown':
        model_correct = (top_1 == true_label)
        final_correct = (final_resolved == true_label)
    else:
        model_correct = None
        final_correct = None

    log_record = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'poem_text': poem_text.strip().replace('\n', ' // '),
        'true_label_if_known': true_label if true_label else 'Unknown',
        'model_prediction': top_1,
        'model_probability': round(prob_1, 2),
        'model_second_best': top_2 if top_2 else 'N/A',
        'model_second_prob': round(prob_2, 2) if prob_2 else 0.0,
        'was_ambiguous': was_ambiguous,
        'user_expert_choice': user_choice if user_choice not in (None, 'None') else None,
        'final_system_result': final_resolved,
        'matched_model_and_user': matched,
        'model_correct_vs_true': model_correct,
        'final_correct_vs_true': final_correct
    }

    df_new = pd.DataFrame([log_record])
    if os.path.exists(LOG_FILENAME):
        df_old = pd.read_csv(LOG_FILENAME)
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.to_csv(LOG_FILENAME, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(LOG_FILENAME, index=False, encoding='utf-8-sig')


# ---------------------------------------------------------------------
# ۶. تابع ارزیابی تعاملی شعر جدید
# ---------------------------------------------------------------------
def evaluate_poem_interactive(poem_text, true_label=None):
    if not poem_text or not str(poem_text).strip():
        print("⚠️ متن شعر خالی است.")
        return

    vec_input = vectorizer.transform([poem_text])
    probs = clf_model.predict_proba(vec_input)[0]
    classes = le.classes_

    sorted_idx = np.argsort(probs)[::-1]

    top_style_1 = classes[sorted_idx[0]]
    prob_1 = probs[sorted_idx[0]] * 100

    if len(sorted_idx) > 1:
        top_style_2 = classes[sorted_idx[1]]
        prob_2 = probs[sorted_idx[1]] * 100
        diff = prob_1 - prob_2
    else:
        top_style_2 = "N/A"
        prob_2 = 0.0
        diff = 100.0

    print("=" * 65)
    print("📜 متن ورودی:")
    print(poem_text.strip())
    print("=" * 65)
    print(f"🤖 پیش‌بینی مدل: 【 {top_style_1} 】 با احتمال {prob_1:.1f}%")
    if top_style_2 != "N/A":
        print(f"   گزینه دوم:     {top_style_2} با احتمال {prob_2:.1f}% "
              f"(اختلاف: {diff:.1f} واحد درصد)")

    was_ambiguous = False
    user_choice_style = None
    final_style = top_style_1          # پیش‌فرض = پیش‌بینی مدل

    THRESHOLD_DIFF = 20.0              # قاعده تصمیم‌گیری برنامه‌نویس (نه استاندارد آماری)

    if diff < THRESHOLD_DIFF:
        was_ambiguous = True
        print("\n" + "⚡" * 3 +
              f" ابهام تشخیصی: اختلاف دو گزینه برتر کمتر از {THRESHOLD_DIFF} واحد درصد است. " +
              "⚡" * 3)
        print("لطفاً مشخصه بارز سبک‌شناختی شعر را انتخاب کنید:\n")
        print("  [1] خراسانی (واژگان کهن، زبان حماسی و توصیفی)")
        print("  [2] عراقی (غزل، عرفان، عشق و مضامین رندانه)")
        print("  [3] هندی (نازک‌اندیشی و مضمون‌پردازی پیچیده)")
        print("  [4] بازگشت ادبی (بازآفرینی و تقلید هوشمندانه از سبک کهن)")
        print("  [5] معاصر (زبان و ساختار شعر نو یا معاصر)")

        user_ans = input("شماره گزینه (1 تا 5): ").strip()

        mapping = {
            '1': 'Khorasani',
            '2': 'Iraqi',
            '3': 'Indian',
            '4': 'Literary_Return',
            '5': 'Contemporary'
        }

        if user_ans in mapping:
            user_choice_style = mapping[user_ans]
            final_style = user_choice_style
            print(f"\n👤 نظر کاربر ثبت شد: 【 {user_choice_style} 】")
            print("   (این نظر به‌عنوان انتخاب جداگانه ذخیره می‌شود و جایگزین پیش‌بینی مدل نیست)")
        else:
            print("\n⚠️ ورودی نامعتبر. پیش‌بینی مدل بدون تغییر باقی ماند.")
    else:
        print(f"\n✨ اختلاف دو گزینه برتر ≥ {THRESHOLD_DIFF} واحد درصد؛ "
              "مدل بدون پرسش از کاربر تصمیم گرفت.")
        print("   (توجه: این اختلاف لزوماً به معنای کالیبره بودن احتمال‌ها یا صحت پیش‌بینی نیست.)")

    print("=" * 65)

    # ثبت لاگ با تفکیک کامل
    log_thesis_evaluation(
        poem_text=poem_text,
        true_label=true_label,
        top_1=top_style_1,
        prob_1=prob_1,
        top_2=top_style_2,
        prob_2=prob_2,
        was_ambiguous=was_ambiguous,
        user_choice=user_choice_style,
        final_resolved=final_style
    )

    print(f"💾 رکورد در فایل «{LOG_FILENAME}» ذخیره شد.")
    print("=" * 65)


# ---------------------------------------------------------------------
# ۷. نمونه تست (بیت حافظ با برچسب مرجع فرضی)
# ---------------------------------------------------------------------
test_hafez = """
خرم آن روز کز این منزل ویران بروم
راحت جان طلبم وز پی جانان بروم
"""

evaluate_poem_interactive(test_hafez, true_label="Iraqi")
