import os
import uuid
import json
from translations import translations
from config import BOT_TOKEN, UPLOAD_FOLDER
from models import SessionLocal, init_db, User, Resume
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import telebot
from telebot import types

# === CONFIG ===
PAYPAL_URL = "https://paypal.me/chetresky/15"
TARIFFS = {
    "basic": {"price": 0, "desc": "Бесплатная версия"},
    "plus": {"price": 15, "desc": "Премиум PDF без водяного знака"}
}

# === SETUP ===
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
init_db()
bot = telebot.TeleBot(BOT_TOKEN)

# in-memory flow state
flow_state = {}  # chat_id -> dict(step, resume_id)

# === TRANSLATION HELPER ===
def t(key, lang="ru"):
    return translations.get(key, {}).get(lang, translations.get(key, {}).get("ru", ""))

# === DB HELPERS ===
def get_or_create_user(db, telegram_id, lang="ru"):
    user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
    if not user:
        user = User(telegram_id=str(telegram_id), lang=lang)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def _get_lang_for_chat(chat_id):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(chat_id)).first()
    lang = user.lang if user else "ru"
    db.close()
    return lang

# === COMMANDS ===

@bot.message_handler(commands=['start'])
def cmd_start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("🇷🇺 Русский", "🇱🇹 Lietuvių", "🇬🇧 English")
    bot.send_message(message.chat.id, t("choose_language", "ru"), reply_markup=keyboard)
    flow_state[message.chat.id] = "choose_language"

@bot.message_handler(func=lambda m: flow_state.get(m.chat.id) == "choose_language")
def handle_choose_language(message):
    text = message.text
    lang = "ru"
    if "Рус" in text:
        lang = "ru"
    elif "Liet" in text:
        lang = "lt"
    elif "Eng" in text:
        lang = "en"
    db = SessionLocal()
    get_or_create_user(db, message.chat.id, lang=lang)
    db.close()

    flow_state[message.chat.id] = {"step": "ask_name"}
    bot.send_message(message.chat.id, t("start_name", lang), reply_markup=types.ReplyKeyboardRemove())

# === RESUME CREATION FLOW ===

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_name")
def handle_name(message):
    lang = _get_lang_for_chat(message.chat.id)
    db = SessionLocal()
    user = get_or_create_user(db, message.chat.id, lang)
    resume = Resume(user_id=user.id)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    flow_state[message.chat.id] = {"step": "ask_city", "resume_id": resume.id}
    resume.name = message.text
    db.commit()
    db.close()
    bot.send_message(message.chat.id, t("ask_city", lang))

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_city")
def handle_city(message):
    _save_field_and_ask_next(message, "city", "ask_position", "ask_position")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_position")
def handle_position(message):
    _save_field_and_ask_next(message, "position", "ask_experience", "ask_experience")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_experience")
def handle_experience(message):
    _save_field_and_ask_next(message, "experience", "ask_education", "ask_education")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_education")
def handle_education(message):
    _save_field_and_ask_next(message, "education", "ask_skills", "ask_skills")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_skills")
def handle_skills(message):
    _save_field_and_ask_next(message, "skills", "ask_consent", "ask_consent")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_consent")
def handle_consent(message):
    lang = _get_lang_for_chat(message.chat.id)
    state = flow_state[message.chat.id]
    text = message.text.strip().lower()
    positive = text in ["да", "yes", "y", "taip", "t"]
    db = SessionLocal()
    resume = db.query(Resume).get(state["resume_id"])
    resume.consent_for_employers = positive
    db.commit()

    # === PDF creation ===
    pdf_path = generate_pdf_and_save(resume, lang)
    resume.pdf_path = pdf_path
    db.commit()
    db.close()

    flow_state.pop(message.chat.id, None)
    bot.send_document(message.chat.id, open(pdf_path, "rb"))
    bot.send_message(message.chat.id, t("resume_ready", lang))
    bot.send_message(message.chat.id, t("thanks", lang))
    bot.send_message(message.chat.id, t("upgrade_offer", lang) + f"\n👉 {PAYPAL_URL}")

# === PDF GENERATOR ===

def generate_pdf_and_save(resume_obj, lang="ru"):
    filename = f"{uuid.uuid4().hex}.pdf"
    path = os.path.join(UPLOAD_FOLDER, filename)
    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("DejaVu", 14)
    titles = {"ru":"РЕЗЮМЕ","en":"RESUME","lt":"GYVENIMO APRAŠYMAS"}
    labels = {
        "ru": ["Имя", "Город", "Позиция", "Опыт", "Образование", "Навыки"],
        "en": ["Name", "City", "Position", "Experience", "Education", "Skills"],
        "lt": ["Vardas", "Miestas", "Pareigos", "Patirtis", "Išsilavinimas", "Įgūdžiai"]
    }
    y = 780
    c.setFont("DejaVu", 18)
    c.drawString(220, 820, titles.get(lang, "RESUME"))
    c.setFont("DejaVu", 12)
    entries = [
        resume_obj.name or "",
        resume_obj.city or "",
        resume_obj.position or "",
        resume_obj.experience or "",
        resume_obj.education or "",
        resume_obj.skills or ""
    ]
    for label, value in zip(labels.get(lang, labels["ru"]), entries):
        c.drawString(60, y, f"{label}: {value}")
        y -= 22

    # watermark for free version
    if not resume_obj.consent_for_employers:
        c.setFont("DejaVu", 36)
        c.setFillGray(0.85)
        c.drawString(160, 400, "DEMO VERSION")

    c.save()
    return path

# === SHORT HELPERS ===

def _get_step(chat_id):
    state = flow_state.get(chat_id)
    if isinstance(state, dict):
        return state.get("step")
    return state

def _save_field_and_ask_next(message, field, next_step, next_key):
    lang = _get_lang_for_chat(message.chat.id)
    state = flow_state[message.chat.id]
    db = SessionLocal()
    resume = db.query(Resume).get(state["resume_id"])
    setattr(resume, field, message.text)
    db.commit()
    db.close()
    state["step"] = next_step
    bot.send_message(message.chat.id, t(next_key, lang))

# === EXTRA COMMANDS ===

@bot.message_handler(commands=['upgrade'])
def cmd_upgrade(message):
    lang = _get_lang_for_chat(message.chat.id)
    texts = {
        "ru": "💎 Получи профессиональное резюме без водяных знаков! Стоимость: 15 €. Оплата через PayPal:",
        "lt": "💎 Gauk profesionalų CV be vandens ženklų! Kaina: 15 €. Mokėjimas per PayPal:",
        "en": "💎 Get a professional resume without watermark! Price: 15 €. Pay via PayPal:"
    }
    bot.send_message(message.chat.id, f"{texts.get(lang, texts['en'])}\n👉 {PAYPAL_URL}")

@bot.message_handler(commands=['myresumes'])
def cmd_myresumes(message):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(message.chat.id)).first()
    if not user:
        bot.send_message(message.chat.id, "No data")
        db.close()
        return
    out = []
    for r in user.resumes:
        out.append(f"#{r.id} {r.position or '—'} — consent: {r.consent_for_employers}")
    bot.send_message(message.chat.id, "\n".join(out) if out else "No resumes")
    db.close()

@bot.message_handler(commands=['delete_me'])
def cmd_delete_me(message):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(message.chat.id)).first()
    if not user:
        bot.send_message(message.chat.id, "Nothing to delete")
        db.close()
        return
    for r in user.resumes:
        if r.pdf_path and os.path.exists(r.pdf_path):
            os.remove(r.pdf_path)
        db.delete(r)
    db.delete(user)
    db.commit()
    db.close()
    bot.send_message(message.chat.id, "Your data removed (GDPR)")

# === RUN ===
if __name__ == "__main__":
    print("ResumeBot is running ✅")
    bot.polling(none_stop=True, interval=1, timeout=30)
