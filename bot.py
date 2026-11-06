"""
Telegram Bot handlers and command registration.
"""

import logging
from datetime import datetime
import telebot
from telebot import types
import config
from models import Contest
from storage import NotifiedStore
from formatter import format_contest_notice
from scheduler import fetch_all_upcoming_contests, check_and_notify

logger = logging.getLogger(__name__)


def create_bot() -> telebot.TeleBot:
    """Initializes TeleBot instance."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is empty. Please set it in .env file.")
    return telebot.TeleBot(config.TELEGRAM_BOT_TOKEN, parse_mode=None)


def register_handlers(bot: telebot.TeleBot, store: NotifiedStore):
    """Registers all command handlers for the bot."""

    @bot.message_handler(commands=["start", "help"])
    def handle_start(message: types.Message):
        text = (
            "🤖 *DIU ACM Contest Reminder Bot*\n\n"
            "I automatically monitor Codeforces and AtCoder contests and send reminder notices "
            "1 day (24 hours) before each contest starts.\n\n"
            "📌 *Available Commands:*\n"
            "/upcoming - List all upcoming contests\n"
            "/test - Send a preview notice in the exact template\n"
            "/check - Trigger immediate check for contests starting in <= 24h\n"
            "/status - View bot settings and statistics\n"
            "/help - Show this message\n\n"
            "Happy coding 🖤"
        )
        bot.reply_to(message, text, parse_mode="Markdown")

    @bot.message_handler(commands=["upcoming"])
    def handle_upcoming(message: types.Message):
        status_msg = bot.reply_to(message, "⏳ Fetching upcoming contests from Codeforces & AtCoder...")
        try:
            contests = fetch_all_upcoming_contests()
            if not contests:
                bot.edit_message_text(
                    "No upcoming contests found at this time.",
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                )
                return

            now = datetime.now(config.TZ)
            lines = ["🏆 *Upcoming Contests:*\n"]

            for c in contests[:12]:  # show up to 12
                hours_left = c.hours_until_start(now)
                dt = c.start_time
                date_str = f"{dt.strftime('%a')}, {dt.day} {dt.strftime('%b %Y')}"
                time_str = f"{int(dt.strftime('%I'))}:{dt.strftime('%M')} {dt.strftime('%p')}"
                tag = "CF" if c.platform == "codeforces" else "AC"

                lines.append(
                    f"• *[{tag}]* [{c.name}]({c.link})\n"
                    f"   📅 {date_str} at {time_str} ({config.TIMEZONE_NAME})\n"
                    f"   ⏳ Starts in: {hours_left:.1f} hours\n"
                )

            lines.append(f"_Times shown in {config.TIMEZONE_NAME} (UTC+6)_")

            bot.edit_message_text(
                "\n".join(lines),
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error("Error in /upcoming handler: %s", e)
            bot.edit_message_text(
                f"❌ Failed to fetch upcoming contests: {e}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
            )

    @bot.message_handler(commands=["test"])
    def handle_test(message: types.Message):
        """Sends a live preview of the exact notice template to this chat."""
        try:
            contests = fetch_all_upcoming_contests()
            cf_contest = next((c for c in contests if c.platform == "codeforces"), None)
            ac_contest = next((c for c in contests if c.platform == "atcoder"), None)

            sent_any = False
            if cf_contest:
                bot.send_message(
                    message.chat.id,
                    format_contest_notice(cf_contest),
                    disable_web_page_preview=config.DISABLE_WEB_PAGE_PREVIEW,
                )
                sent_any = True

            if ac_contest:
                bot.send_message(
                    message.chat.id,
                    format_contest_notice(ac_contest),
                    disable_web_page_preview=config.DISABLE_WEB_PAGE_PREVIEW,
                )
                sent_any = True

            if not sent_any:
                bot.reply_to(message, "No upcoming contests found to preview.")
        except Exception as e:
            logger.error("Error in /test handler: %s", e)
            bot.reply_to(message, f"❌ Error generating preview: {e}")

    @bot.message_handler(commands=["check"])
    def handle_check(message: types.Message):
        """Runs immediate check and notifies configured channels."""
        status_msg = bot.reply_to(message, "🔍 Checking contests starting in <= 24 hours...")
        try:
            notified = check_and_notify(bot, store)
            if notified:
                summary = "\n".join([f"• [{c.platform.upper()}] {c.name}" for c in notified])
                bot.edit_message_text(
                    f"✅ Sent reminders for {len(notified)} contest(s):\n{summary}",
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                )
            else:
                bot.edit_message_text(
                    "ℹ️ No new contests starting within 24 hours need reminders right now.",
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                )
        except Exception as e:
            logger.error("Error in /check handler: %s", e)
            bot.edit_message_text(
                f"❌ Error during check: {e}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
            )

    @bot.message_handler(commands=["status"])
    def handle_status(message: types.Message):
        text = (
            "⚙️ *Bot Status:*\n\n"
            f"• *Timezone:* `{config.TIMEZONE_NAME}`\n"
            f"• *Reminder Window:* `{config.REMINDER_HOURS_BEFORE} hours (1 day)`\n"
            f"• *Check Interval:* `{config.CHECK_INTERVAL_MINUTES} minutes`\n"
            f"• *Target Chat(s):* `{', '.join(config.TELEGRAM_CHAT_IDS) if config.TELEGRAM_CHAT_IDS else 'Not configured'}`\n"
            f"• *Notified Contests Tracked:* `{store.get_notified_count()}`\n"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
