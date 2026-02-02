import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

SHEET_NAME = os.getenv("SHEET_NAME", "ResumeBot_Data")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./resumebot.db"
)

ADMIN_API_KEY = os.getenv(
    "ADMIN_API_KEY",
    "change_this_to_strong_key"
)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")

FONT_PATH = os.getenv(
    "FONT_PATH",
    "./fonts/DejaVuSans.ttf"
)

PAYPAL_URL = "https://paypal.me/chetresky/15"

TARIFFS = {
    "basic": {
        "price": 0,
        "desc": "Бесплатная версия"
    },
    "plus": {
        "price": 15,
        "desc": "Премиум PDF с профессиональным дизайном"
    }
}
