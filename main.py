import os
import uuid
from translations import translations
from config import BOT_TOKEN, UPLOAD_FOLDER
from models import SessionLocal, init_db, User, Resume

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import telebot
from telebot import types

# ================= CONFIG =================

PAYPAL_URL = "https://paypal.me/chetresky/15"

TARIFFS = {
    "basic": {"price": 0, "desc": "Бесплатная версия"},
    "plus": {"price": 15, "desc": "Премиум PDF без водяного знака"}
}

# ================= PATHS =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "DejaVuSans.ttf")

# ================= SETUP =================

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(FONT_PATH):
    raise FileNotFoundError(f"Font not found: {FONT_PATH}")

pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))

init_db()
bot = telebot.TeleBot(BOT_TOKEN)

# in-memory state
flow_state = {}  # chat_id -> dict(step, resume_id)

# ================= TRANSLATIONS =================

def t(key, lang="ru"):
    return translations.get(key, {}).get(
        lang,
        translations.get(key, {}).get("ru", "")
    )

# ================= DB HELPERS =================

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

# ================= COMMANDS =================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("🇷🇺 Русский", "🇱🇹 Lietuvių", "🇬🇧 English")
    bot.send_message(message.chat.id, t("choose_language", "ru"), reply_markup=keyboard)
    flow_state[message.chat.id] = "choose_language"

@bot.message_handler(func=lambda m: flow_state.get(m.chat.id) == "choose_language")
def handle_choose_language(message):
    text = message.text.lower()
    lang = "ru"
    if "liet" in text:
        lang = "lt"
    elif "eng" in text:
        lang = "en"

    db = SessionLocal()
    get_or_create_user(db, message.chat.id, lang)
    db.close()

    flow_state[message.chat.id] = {"step": "ask_name"}
    bot.send_message(
        message.chat.id,
        t("start_name", lang),
        reply_markup=types.ReplyKeyboardRemove()
    )

# ================= RESUME FLOW =================

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_name")
def handle_name(message):
    lang = _get_lang_for_chat(message.chat.id)
    db = SessionLocal()

    user = get_or_create_user(db, message.chat.id, lang)
    resume = Resume(user_id=user.id, name=message.text)

    db.add(resume)
    db.commit()
    db.refresh(resume)
    db.close()

    flow_state[message.chat.id] = {"step": "ask_city", "resume_id": resume.id}
    bot.send_message(message.chat.id, t("ask_city", lang))

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_city")
def handle_city(message):
    _save_field_and_ask_next(message, "city", "ask_position")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_position")
def handle_position(message):
    _save_field_and_ask_next(message, "position", "ask_experience")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_experience")
def handle_experience(message):
    _save_field_and_ask_next(message, "experience", "ask_education")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_education")
def handle_education(message):
    _save_field_and_ask_next(message, "education", "ask_skills")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_skills")
def handle_skills(message):
    _save_field_and_ask_next(message, "skills", "ask_consent")

@bot.message_handler(func=lambda m: _get_step(m.chat.id) == "ask_consent")
def handle_consent(message):
    lang = _get_lang_for_chat(message.chat.id)
    state = flow_state[message.chat.id]

    positive = message.text.strip().lower() in [
        "да", "yes", "y", "taip", "t"
    ]

    db = SessionLocal()
    resume = db.query(Resume).get(state["resume_id"])
    resume.consent_for_employers = positive
    db.commit()

    pdf_path = generate_pdf_and_save(resume, lang)
    resume.pdf_path = pdf_path
    db.commit()
    db.close()

    flow_state.pop(message.chat.id, None)

    with open(pdf_path, "rb") as f:
        bot.send_document(message.chat.id, f)

    bot.send_message(message.chat.id, t("resume_ready", lang))
    bot.send_message(message.chat.id, t("thanks", lang))
    bot.send_message(
        message.chat.id,
        t("upgrade_offer", lang) + f"\n👉 {PAYPAL_URL}"
    )

# ================= PDF =================

def generate_pdf_and_save(resume, lang="ru"):
    filename = f"{uuid.uuid4().hex}.pdf"
    path = os.path.join(UPLOAD_FOLDER, filename)

    c = canvas.Canvas(path, pagesize=A4)

    titles = {
        "ru": "РЕЗЮМЕ",
        "en": "RESUME",
        "lt": "GYVENIMO APRAŠYMAS"
    }

    labels = {
        "ru": ["Имя", "Город", "Позиция", "Опыт", "Образование", "Навыки"],
        "en": ["Name", "City", "Position", "Experience", "Education", "Skills"],
        "lt": ["Vardas", "Miestas", "Pareigos", "Patir]()
