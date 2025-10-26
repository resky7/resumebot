import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_NAME = os.getenv("SHEET_NAME", "ResumeBot_Data")
# DB: set DATABASE_URL like "postgresql://user:pass@host:5432/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resumebot.db")
# Simple admin API key for the dashboard endpoints (change to a strong secret)
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change_this_to_strong_key")

# Stripe - placeholders (fill if you will use Stripe)
STRIPE_SECRET = os.getenv("STRIPE_SECRET", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Upload folder
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
TARIFFS = {
  "basic": {"price": 0, "desc": "Бесплатная версия"},
  "plus": {"price": 15, "desc": "Премиум PDF с профессиональным дизайном"}
}
PAYPAL_URL = "https://paypal.me/chetresky/15"

