import os
import smtplib
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request

GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
EMAIL = "podlesnykhdn@gmail.com"
lesson_num = int(os.environ.get("LESSON_NUM", "1"))
today = datetime.now().strftime("%d.%m.%Y")

# --- Load lesson ---
with open("lessons.json", encoding="utf-8") as f:
    lessons = json.load(f)
idx = (lesson_num - 1) % len(lessons)
lesson = lessons[idx]

# --- Fetch RSS news ---
RSS_FEEDS = [
    ("РБК", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"),
    ("Интерфакс", "https://www.interfax.ru/rss.asp"),
]
TICKERS = ["x5", "five", "лента", "lent", "сбербанк", "sber", "novabev", "belu", "золото", "moex", "биржа", "акци"]

news_items = []
for source_name, url in RSS_FEEDS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read())
        for item in root.findall(".//item")[:40]:
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is None:
                continue
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip() if link_el is not None else ""
            if any(t in title.lower() for t in TICKERS):
                news_items.append({"source": source_name, "title": title, "link": link})
            if len(news_items) >= 6:
                break
    except Exception as e:
        print(f"RSS ошибка {source_name}: {e}")
    if len(news_items) >= 6:
        break

if news_items:
    news_html = "".join(
        f'<p style="margin:6px 0;color:#374151;">• <a href="{i["link"]}" style="color:#2563eb;text-decoration:none;">{i["title"]}</a> <span style="color:#9ca3af;font-size:11px;">({i["source"]})</span></p>'
        for i in news_items
    )
else:
    news_html = '<p style="color:#9ca3af;font-size:13px;">Новостей по позициям портфеля сегодня не найдено.</p>'

def to_html(text):
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            result.append("<br>")
        elif line.startswith("**") and line.endswith("**"):
            result.append(f'<p style="margin:8px 0;"><strong style="color:#1e3a5f;">{line.strip("*")}</strong></p>')
        else:
            line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            result.append(f'<p style="margin:6px 0;color:#374151;">{line}</p>')
    return "\n".join(result)

html_body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
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
      {news_html}
      <div style="margin-top:16px;padding:12px;background:#f0fdf4;border-radius:8px;border:1px solid #bbf7d0;">
        <p style="margin:0;font-size:12px;color:#166534;"><strong>Портфель:</strong> X5 (42) · Лента (53) · Сбербанк (74) · Novabev (12) · TGLD (4618) · ~280 000 ₽</p>
      </div>
    </div>
  </div>
  <div style="background:#f3f4f6;padding:14px 24px;border-radius:0 0 10px 10px;border:1px solid #e5e7eb;border-top:none;">
    <p style="color:#9ca3af;font-size:11px;margin:0;text-align:center;">my_prodject_invest · github.com/podlesnykhdn/my_prodject_invest</p>
  </div>
</body></html>"""

print("Отправляю письмо через Gmail...")
msg = MIMEMultipart("alternative")
msg["Subject"] = f"📈 Урок #{lesson_num}: {lesson['title']} · {today}"
msg["From"] = EMAIL
msg["To"] = EMAIL
msg.attach(MIMEText(html_body, "html", "utf-8"))

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.ehlo()
    server.starttls()
    server.login(EMAIL, GMAIL_PASSWORD)
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    print("Письмо отправлено!")
