"""
Configuration settings for ACM Contest Reminder Bot.
"""

import os
import zoneinfo
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Destination Chat / Channel ID(s)
# Can be single ID or comma-separated list
_raw_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_CHAT_IDS = [cid.strip() for cid in _raw_chat_id.split(",") if cid.strip()]

# Timezone
TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Dhaka").strip()
try:
    TZ = zoneinfo.ZoneInfo(TIMEZONE_NAME)
except Exception:
    TZ = zoneinfo.ZoneInfo("Asia/Dhaka")

# Periodic Check Interval (in minutes)
try:
    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
except ValueError:
    CHECK_INTERVAL_MINUTES = 15

# Reminder window in hours (default 24 hours = 1 day before)
try:
    REMINDER_HOURS_BEFORE = float(os.getenv("REMINDER_HOURS_BEFORE", "24.0"))
except ValueError:
    REMINDER_HOURS_BEFORE = 24.0

# Telegram Web Page Preview
DISABLE_WEB_PAGE_PREVIEW = os.getenv("DISABLE_WEB_PAGE_PREVIEW", "true").lower() in ("true", "1", "yes")

# Storage file path
STORAGE_FILE = BASE_DIR / "notified_contests.json"
