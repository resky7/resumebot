import os
from dotenv import load_dotenv

load_dotenv()

# ================= BASIC =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= DATABASE =================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./resumebot.db"
)

# ================= ADMIN =================

ADMIN_API_KEY = os.getenv(
    "ADMIN_API_KEY",
    "change_this_to_strong_key"
)

# ================= PATHS =================

UPLOAD_FOLDER = os.getenv(
    "UPLOAD_FOLDER",
    os.path.join(BASE_DIR, "uploads")
)

FONT_PATH = os.path.join(
    BASE_DIR,
    "fonts",
    "DejaVuSans.ttf"
)

# ================= BUSINESS =================

PAYPAL_URL = "https://paypal.me/chetresky/15"

TARIFFS = {
    "basic": {
        "price": 0,
        "desc": "Бесплатная версия"
    },
    "plus": {
        "price": 15,
        "desc": "Премиум PDF без водяного знака"
    }
}
