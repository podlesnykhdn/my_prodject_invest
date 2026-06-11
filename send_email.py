import os
import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
TO_EMAIL = "podlesnykhdn@gmail.com"
lesson_num = int(os.environ.get("LESSON_NUM", "1"))
today = datetime.now().strftime("%d.%m.%Y")

# --- Load lesson from lessons.json ---
with open("lessons.json", encoding="utf-8") as f:
    lessons = json.load(f)

# Cycle through lessons (1-15 repeat)
idx = (lesson_num - 1) % len(lessons)
lesson = lessons[idx]

# --- Fetch news from RSS feeds ---
RSS_FEEDS = [
    ("РБК Инвестиции", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"),
    ("Интерфакс", "https://www.interfax.ru/rss.asp"),
]

TICKERS = ["X5", "FIVE", "Лента", "LENT", "Сбербанк", "SBER", "Novabev", "BELU", "золото", "MOEX", "биржа"]

news_items = []
for source_name, url in RSS_FEEDS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        for item in root.findall(".//item")[:30]:
            title_el = item.find("title")
            desc_el = item.find("description")
            link_el = item.find("link")
            if title_el is None:
                continue
            title = title_el.text or ""
            desc = desc_el.text or "" if desc_el is not None else ""
            link = link_el.text or "" if link_el is not None else ""
            combined = (title + " " + desc).lower()
            for ticker in TICKERS:
                if ticker.lower() in combined:
                    news_items.append({
                        "source": source_name,
                        "title": title.strip(),
                        "link": link.strip()
                    })
                    break
            if len(news_items) >= 5:
                break
    except Exception as e:
        print(f"RSS {source_name} error: {e}")
    if len(news_items) >= 5:
        break

# Format news block
if news_items:
    news_html = ""
    for item in news_items[:5]:
        news_html += f'<p style="margin:6px 0;color:#374151;">• <a href="{item["link"]}" style="color:#2563eb;text-decoration:none;">{item["title"]}</a> <span style="color:#9ca3af;font-size:11px;">({item["source"]})</span></p>\n'
else:
    news_html = '<p style="color:#9ca3af;">Актуальных новостей по портфелю не найдено.</p>'

# Format lesson text
def to_html(text):
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            result.append("<br>")
            continue
        if line.startswith("**") and line.endswith("**"):
            result.append(f'<p style="margin:8px 0;"><strong style="color:#1e3a5f;">{line.strip("*")}</strong></p>')
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
      <p style="color:#2563eb;font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin:0 0 4px;">🎓 Ментор · Урок №{lesson_num}</p>
      <h2 style="font-size:16px;color:#1e3a5f;margin:0 0 12px;">{lesson["title"]}</h2>
      {to_html(lesson["text"])}
    </div>

    <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">

    <div style="border-left:4px solid #059669;padding-left:16px;">
      <p style="color:#059669;font-size:11px;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">📊 Аналитик · Новости по портфелю</p>
      <p style="color:#6b7280;font-size:12px;margin:0 0 10px;">Актуальные новости касающиеся твоих позиций:</p>
      {news_html}
      <div style="margin-top:16px;padding:12px;background:#f0fdf4;border-radius:8px;border:1px solid #bbf7d0;">
        <p style="margin:0;font-size:12px;color:#166534;"><strong>Твой портфель:</strong> X5 (42 акц.) · Лента (53 акц.) · Сбербанк (74 акц.) · Novabev (12 акц.) · TGLD (4618 паёв) · ~280 000 ₽</p>
      </div>
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
    "subject": f"📈 Урок #{lesson_num}: {lesson['title']} · {today}",
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
