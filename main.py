"""
Entry point for DIU ACM Contest Reminder Bot.
"""

import sys
import argparse
import logging
import threading
import time
import requests

import config
from storage import NotifiedStore
from models import Contest
from formatter import format_contest_notice
from scheduler import (
    fetch_all_upcoming_contests,
    check_and_notify,
    run_scheduler_worker,
    send_notice_to_chats,
)
from bot import create_bot, register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def print_banner():
    banner = r"""
  ___  ____ __  __   ____   ___ _____ 
 / _ \/ ___|  \/  | | __ ) / _ \_   _|
| | | \___ \ |\/| | |  _ \| | | || |  
| |_| |___) | |  | | | |_) | |_| || |  
 \__\_\____/|_|  |_| |____/ \___/ |_|  
     ACM Contest Reminder Bot
    """
    print(banner)


def cmd_upcoming():
    """Prints all upcoming contests to the terminal."""
    print("⏳ Fetching upcoming contests from Codeforces & AtCoder...\n")
    contests = fetch_all_upcoming_contests()
    if not contests:
        print("No upcoming contests found.")
        return

    from datetime import datetime
    now = datetime.now(config.TZ)

    print(f"{'Platform':<12} | {'Contest Name':<38} | {'Start Time (BST)':<22} | {'Starts In'}")
    print("-" * 90)
    for c in contests:
        hours_left = c.hours_until_start(now)
        dt = c.start_time
        date_str = f"{dt.strftime('%a')}, {dt.day} {dt.strftime('%b')} {int(dt.strftime('%I'))}:{dt.strftime('%M %p')}"
        starts_in = f"{hours_left:.1f}h"
        print(f"{c.platform.capitalize():<12} | {c.name[:36]:<38} | {date_str:<22} | {starts_in}")


def cmd_get_chat_id():
    """Helper to discover Telegram Chat ID or Channel ID."""
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not configured in .env")
        print("Please set your bot token from @BotFather in .env first.")
        return

    print("🔍 Checking recent updates from Telegram Bot API...")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            print(f"❌ Telegram API returned error: {data.get('description')}")
            return

        results = data.get("result", [])
        if not results:
            print("\n⚠️ No messages found!")
            print("👉 To find your Chat ID:")
            print("   1. Open Telegram and search for your bot username.")
            print("   2. Click 'Start' or send any message like 'hello' to your bot.")
            print("   3. (For Channels) Add your bot as an Administrator to your channel and post a message.")
            print("   4. Re-run this command: python main.py --get-chat-id\n")
            return

        print(f"\n✅ Found {len(results)} recent update(s):")
        seen_chats = set()
        for u in results:
            chat = None
            if "message" in u:
                chat = u["message"]["chat"]
            elif "channel_post" in u:
                chat = u["channel_post"]["chat"]
            elif "my_chat_member" in u:
                chat = u["my_chat_member"]["chat"]

            if chat:
                cid = chat["id"]
                if cid not in seen_chats:
                    seen_chats.add(cid)
                    ctype = chat.get("type", "unknown")
                    title = chat.get("title") or chat.get("username") or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                    print(f"   • Chat Title/Name: {title}")
                    print(f"     Chat ID:         {cid}")
                    print(f"     Type:            {ctype}")
                    print(f"     Use in .env:     TELEGRAM_CHAT_ID={cid}\n")

    except Exception as e:
        print(f"❌ Failed to reach Telegram API: {e}")


def cmd_test_message(store: NotifiedStore):
    """Sends a sample notice to the configured TELEGRAM_CHAT_IDS."""
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is not configured in .env")
        return
    if not config.TELEGRAM_CHAT_IDS:
        print("❌ Error: TELEGRAM_CHAT_ID is not configured in .env")
        return

    print(f"📡 Fetching next contest to send preview notice to {config.TELEGRAM_CHAT_IDS}...")
    contests = fetch_all_upcoming_contests()
    if not contests:
        print("❌ No upcoming contests found to send preview.")
        return

    target_contest = contests[0]
    message = format_contest_notice(target_contest)

    print("\nPreviewing message:")
    print("-" * 50)
    print(message)
    print("-" * 50)

    try:
        bot = create_bot()
        sent = send_notice_to_chats(bot, message, config.TELEGRAM_CHAT_IDS)
        if sent:
            print(f"\n✅ Test reminder sent successfully to {config.TELEGRAM_CHAT_IDS}!")
        else:
            print("\n❌ Failed to send test reminder.")
    except Exception as e:
        print(f"\n❌ Error sending message: {e}")


def main():
    parser = argparse.ArgumentParser(description="DIU ACM Contest Reminder Telegram Bot")
    parser.add_argument("--upcoming", action="store_true", help="Print all upcoming contests and exit")
    parser.add_argument("--check", "--once", dest="check_once", action="store_true", help="Run reminder check once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Check contests within 24h and print notices to console without sending")
    parser.add_argument("--force", action="store_true", help="Force send reminder even if already recorded in storage")
    parser.add_argument("--test", action="store_true", help="Send a test contest reminder to Telegram chat")
    parser.add_argument("--get-chat-id", action="store_true", help="Helper to detect your Telegram Chat ID")

    args = parser.parse_args()
    print_banner()

    store = NotifiedStore()

    if args.upcoming:
        cmd_upcoming()
        return

    if args.get_chat_id:
        cmd_get_chat_id()
        return

    if args.test:
        cmd_test_message(store)
        return

    if args.dry_run:
        print("🔍 Running in DRY-RUN mode (no messages sent, storage unchanged)...")
        check_and_notify(bot=None, store=store, dry_run=True, force=args.force)
        return

    if args.check_once:
        print("🔍 Running single check for contests starting within 24 hours...")
        if not config.TELEGRAM_BOT_TOKEN:
            print("⚠️ TELEGRAM_BOT_TOKEN not configured. Running in console mode.")
            check_and_notify(bot=None, store=store, dry_run=True, force=args.force)
            return

        bot = create_bot()
        notified = check_and_notify(bot=bot, store=store, dry_run=False, force=args.force)
        print(f"✅ Single check completed. {len(notified)} reminder(s) sent.")
        return

    # Daemon mode: Start Bot and Scheduler
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN is missing!")
        print("👉 Please copy .env.example to .env and fill in your Bot Token:")
        print("   cp .env.example .env")
        print("   nano .env")
        print("\nTip: To see upcoming contests in terminal, run: python main.py --upcoming")
        print("Tip: To test format without Telegram token, run: python main.py --dry-run")
        sys.exit(1)

    if not config.TELEGRAM_CHAT_IDS:
        print("⚠️ Warning: TELEGRAM_CHAT_ID is not configured in .env.")
        print("Reminders won't have a destination until TELEGRAM_CHAT_ID is set.")
        print("You can run: python main.py --get-chat-id to find your chat/channel ID.\n")

    bot = create_bot()
    register_handlers(bot, store)

    stop_event = threading.Event()

    # Start scheduler in a background daemon thread
    scheduler_thread = threading.Thread(
        target=run_scheduler_worker,
        args=(bot, store, stop_event),
        daemon=True,
    )
    scheduler_thread.start()

    logger.info("Bot starting with polling. Press Ctrl+C to stop.")
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        stop_event.set()
        scheduler_thread.join(timeout=2.0)
        logger.info("Bot shutdown completed.")


if __name__ == "__main__":
    main()
