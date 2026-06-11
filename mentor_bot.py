"""
mentor_bot.py — Telegram бот Ментора
Команды: /start, /lesson, /progress
Отправляет ежедневные уроки по инвестициям.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import date, datetime
from pathlib import Path

TOKEN    = os.environ["MENTOR_BOT_TOKEN"]
CHAT_ID  = os.environ["TELEGRAM_CHAT_ID"]
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs" / "mentor"
LESSONS_FILE = BASE_DIR / "lessons.json"
TODAY    = date.today().isoformat()
MODE     = os.environ.get("BOT_MODE", "morning")  # morning | command

# ─── TELEGRAM API ─────────────────────────────────────────────────────────────

def tg(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def send(text, parse_mode="HTML"):
    return tg("sendMessage", {
        "chat_id":    CHAT_ID,
        "text":       text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    })

# ─── ЛОГИ ─────────────────────────────────────────────────────────────────────

def load_log():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{TODAY}.json"
    if log_file.exists():
        with open(log_file, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_log(data):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{TODAY}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def get_lesson_num():
    """Считаем номер урока по дням с начала проекта."""
    start = date(2026, 6, 6)
    delta = (date.today() - start).days + 6  # стартуем с урока 6
    return max(delta, 1)

# ─── ЗАГРУЗКА УРОКА ───────────────────────────────────────────────────────────

def load_lesson(num):
    with open(LESSONS_FILE, encoding="utf-8") as f:
        lessons = json.load(f)
    idx = (num - 1) % len(lessons)
    return lessons[idx], num

# ─── ФОРМАТИРОВАНИЕ ───────────────────────────────────────────────────────────

def format_lesson(lesson, num):
    text = lesson["text"]
    # Конвертируем **bold** в HTML
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Параграфы
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    body = "\n\n".join(paragraphs)

    return (
        f"🎓 <b>Ментор — Урок #{num}</b>\n"
        f"{'─' * 28}\n"
        f"<b>{lesson['title']}</b>\n\n"
        f"{body}\n\n"
        f"{'─' * 28}\n"
        f"📁 <a href='https://podlesnykhdn.github.io/my_prodject_invest/'>Дашборд портфеля</a>"
    )

def format_progress(num):
    total = 15
    done  = min(num, total)
    pct   = int(done / total * 100)
    bar   = "█" * (done // 2) + "░" * ((total - done) // 2)
    return (
        f"📊 <b>Твой прогресс обучения</b>\n"
        f"{'─' * 28}\n"
        f"Пройдено уроков: {done}/{total}\n"
        f"[{bar}] {pct}%\n\n"
        f"Текущий урок: #{num}\n"
        f"Осталось до конца блока: {total - done} уроков\n\n"
        f"Блоки обучения:\n"
        f"{'✅' if num > 5 else '📍'} Уроки 1-5: Основы акций и биржи\n"
        f"{'✅' if num > 10 else ('📍' if num > 5 else '⬜')} Уроки 6-10: Котировки, дивиденды, P/E\n"
        f"{'✅' if num > 15 else ('📍' if num > 10 else '⬜')} Уроки 11-15: Стратегии и риски"
    )

# ─── ОСНОВНАЯ ЛОГИКА ──────────────────────────────────────────────────────────

def run_morning():
    """Утренняя отправка урока."""
    log = load_log()

    # Лимит: 1 урок в день
    if log.get("morning_sent"):
        print(f"Урок сегодня уже отправлен в {log.get('sent_at')}")
        return

    num = get_lesson_num()
    lesson, num = load_lesson(num)
    msg = format_lesson(lesson, num)

    result = send(msg)
    print(f"Урок #{num} отправлен: {result.get('ok')}")

    save_log({
        "date":         TODAY,
        "lesson_num":   num,
        "lesson_title": lesson["title"],
        "morning_sent": True,
        "sent_at":      datetime.now().strftime("%H:%M"),
        "message_id":   result.get("result", {}).get("message_id"),
    })

def run_command():
    """Обработка входящих команд."""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=5"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as r:
        updates = json.loads(r.read()).get("result", [])

    for update in updates[-5:]:  # последние 5 сообщений
        msg  = update.get("message", {})
        text = msg.get("text", "")
        cid  = str(msg.get("chat", {}).get("id", ""))

        if cid != str(CHAT_ID):
            continue

        if text == "/start":
            send(
                "👋 Привет! Я твой <b>Ментор по инвестициям</b>.\n\n"
                "Каждое утро я буду присылать тебе короткий урок "
                "о фондовом рынке — от основ к стратегиям.\n\n"
                "<b>Команды:</b>\n"
                "/lesson — получить урок прямо сейчас\n"
                "/progress — посмотреть прогресс обучения"
            )

        elif text == "/lesson":
            log = load_log()
            if log.get("morning_sent"):
                # Уже отправляли сегодня — отправим снова по запросу
                num = log.get("lesson_num", get_lesson_num())
            else:
                num = get_lesson_num()
            lesson, num = load_lesson(num)
            send(format_lesson(lesson, num))

        elif text == "/progress":
            num = get_lesson_num()
            send(format_progress(num))

if __name__ == "__main__":
    print(f"Ментор-бот запущен, режим: {MODE}")
    if MODE == "morning":
        run_morning()
    elif MODE == "command":
        run_command()
