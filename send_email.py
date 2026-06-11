import os
import urllib.request
import json
from datetime import datetime

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
TO_EMAIL = "podlesnykhdn@gmail.com"

def ask_groq(prompt):
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

lesson_num = int(os.environ.get("LESSON_NUM", "1"))
today = datetime.now().strftime("%d.%m.%Y")

mentor_prompt = f"""Ты — ментор по инвестициям для абсолютного новичка. Обучай структурированно, шаг за шагом.

Это урок №{lesson_num}. Логика уроков:
- Уроки 1-5: что такое акции, биржа, как всё устроено
- Уроки 6-10: котировки, дивиденды, базовые показатели (P/E и др.)
- Уроки 11+: стратегии, риски, диверсификация

Напиши урок №{lesson_num}. Требования:
- Максимум 250 слов
- Простой язык, без жаргона (или с объяснением)
- Конкретные примеры
- В конце — одна ключевая мысль
- Формат: заголовок, текст, ключевая мысль

Только русский язык."""

analyst_prompt = f"""Ты — инвестиционный аналитик. Давай честную сводку по портфелю начинающего инвестора на Московской бирже.

Портфель (на {today}):
- X5 (Корпоративный центр X5) — 42 акции, дивидендные
- LENT (Лента) — 53 акции, без дивидендов
- SBER (Сбербанк) — 74 акции, дивидендные
- BELU (Novabev Group) — 12 акций, дивидендные
- TGLD (Фонд Золото ТБанк) — 4618 паёв, ETF на золото

Стоимость: ~280 000 ₽. Стратегия: дивидендная, долгосрочная.

По каждой позиции кратко:
1. Общая ситуация с компанией/активом
2. Факторы влияния (ставка ЦБ, санкции, отрасль)
3. Вывод: держать / наблюдать / есть риски

Будь честным — не выдумывай конкретные цены. Максимум 300 слов. Только русский язык."""

print("Запрашиваю урок у Ментора...")
mentor_text = ask_groq(mentor_prompt)

print("Запрашиваю сводку у Аналитика...")
analyst_text = ask_groq(analyst_prompt)

def to_html(text):
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("### ") or line.startswith("## "):
            result.append(f'<h3 style="color:#1d4ed8;font-size:15px;margin:16px 0 6px;">{line.lstrip("#").strip()}</h3>')
        elif line.startswith("**") and line.endswith("**"):
            result.append(f'<p style="margin:6px 0;"><strong>{line.strip("*")}</strong></p>')
        else:
            line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            result.append(f'<p style="margin:6px 0;color:#374151;">{line}</p>')
    return "\n".join(result)

html_email = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9fafb;padding:20px;">

  <div style="background:#1e3a5f;padding:20px 24px;border-radius:10px 10px 0 0;">
    <h1 style="color:#fff;margin:0;font-size:18px;">📈 my_prodject_invest</h1>
    <p style="color:#93c5fd;margin:4px 0 0;font-size:13px;">{today} · Ежедневная рассылка</p>
  </div>

  <div style="background:#fff;padding:24px;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;">

    <div style="border-left:4px solid #2563eb;padding-left:16px;margin-bottom:28px;">
      <p style="color:#2563eb;font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">🎓 Ментор · Урок №{lesson_num}</p>
      {to_html(mentor_text)}
    </div>

    <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">

    <div style="border-left:4px solid #059669;padding-left:16px;">
      <p style="color:#059669;font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">📊 Аналитик · Сводка по портфелю</p>
      {to_html(analyst_text)}
    </div>

  </div>

  <div style="background:#f3f4f6;padding:14px 24px;border-radius:0 0 10px 10px;border:1px solid #e5e7eb;border-top:none;">
    <p style="color:#9ca3af;font-size:11px;margin:0;text-align:center;">
      my_prodject_invest · github.com/podlesnykhdn/my_prodject_invest
    </p>
  </div>

</body>
</html>"""

print("Отправляю письмо...")
payload = json.dumps({
    "from": "my_prodject_invest <onboarding@resend.dev>",
    "to": [TO_EMAIL],
    "subject": f"📈 Урок #{lesson_num} + сводка по портфелю · {today}",
    "html": html_email
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.resend.com/emails",
    data=payload,
    headers={
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    print("Письмо отправлено! ID:", result.get("id"))
