"""
Scheduler and contest reminder worker.
"""

import logging
import time
import threading
from datetime import datetime
from models import Contest
from platforms import fetch_codeforces_contests, fetch_atcoder_contests
from formatter import format_contest_notice
from storage import NotifiedStore
import config

logger = logging.getLogger(__name__)


def fetch_all_upcoming_contests() -> list[Contest]:
    """
    Fetches upcoming contests from all supported platforms (Codeforces, AtCoder)
    and returns them merged and sorted chronologically.
    """
    all_contests: list[Contest] = []

    # Fetch Codeforces
    try:
        cf_contests = fetch_codeforces_contests()
        all_contests.extend(cf_contests)
        logger.info("Fetched %d upcoming contests from Codeforces", len(cf_contests))
    except Exception as e:
        logger.error("Failed to fetch Codeforces contests: %s", e)

    # Fetch AtCoder
    try:
        ac_contests = fetch_atcoder_contests()
        all_contests.extend(ac_contests)
        logger.info("Fetched %d upcoming contests from AtCoder", len(ac_contests))
    except Exception as e:
        logger.error("Failed to fetch AtCoder contests: %s", e)

    # Sort chronologically
    all_contests.sort(key=lambda c: c.start_time)
    return all_contests


def send_notice_to_chats(bot, message: str, chat_ids: list[str]) -> bool:
    """
    Sends a message to the specified chat IDs using the Telegram Bot.
    """
    if not bot or not chat_ids:
        logger.warning("Bot or chat_ids not configured. Message not sent via Telegram.")
        return False

    success_any = False
    for chat_id in chat_ids:
        try:
            bot.send_message(
                chat_id=chat_id,
                text=message,
                disable_web_page_preview=config.DISABLE_WEB_PAGE_PREVIEW,
            )
            logger.info("Contest reminder sent successfully to %s", chat_id)
            success_any = True
            time.sleep(1.0)  # Gentle delay between broadcasts
        except Exception as e:
            logger.error("❌ Failed to send notice to %s: %s", chat_id, e)
            err_msg = str(e).lower()
            if "not a member" in err_msg or "forbidden" in err_msg:
                logger.error(
                    "👉 FIX: Your bot (@%s) MUST be added as an ADMINISTRATOR in '%s' with 'Post Messages' permission!",
                    getattr(bot, "get_me", lambda: None)() and getattr(bot, "get_me", lambda: None)().username or "bot",
                    chat_id,
                )
            elif "chat not found" in err_msg:
                logger.error(
                    "👉 FIX: Chat '%s' was not found. For public channels, use format '@channel_name'.",
                    chat_id,
                )

    return success_any


def check_and_notify(
    bot=None,
    store: NotifiedStore = None,
    dry_run: bool = False,
    force: bool = False,
) -> list[Contest]:
    """
    Checks upcoming contests and sends reminders for any contest
    starting within REMINDER_HOURS_BEFORE (default 24 hours).

    Args:
        bot: TeleBot instance (optional, for sending messages)
        store: NotifiedStore instance
        dry_run: If True, prints messages without sending or saving state
        force: If True, sends reminders even if previously notified

    Returns:
        List of contests that triggered notifications.
    """
    if store is None:
        store = NotifiedStore()

    contests = fetch_all_upcoming_contests()
    now = datetime.now(config.TZ)
    notified_contests: list[Contest] = []

    logger.info(
        "Checking %d contests against reminder window (<= %.1f hours)...",
        len(contests),
        config.REMINDER_HOURS_BEFORE,
    )

    for contest in contests:
        hours_left = contest.hours_until_start(now)

        # Check if contest starts within the reminder window and is still in future
        if 0 < hours_left <= config.REMINDER_HOURS_BEFORE:
            already_sent = store.is_notified(contest)
            if already_sent and not force:
                logger.debug(
                    "Skipping '%s' (starts in %.2fh) - already notified.",
                    contest.name,
                    hours_left,
                )
                continue

            logger.info(
                "Triggering reminder for '%s' (%s, starts in %.2f hours)",
                contest.name,
                contest.platform,
                hours_left,
            )

            message = format_contest_notice(contest)

            if dry_run or bot is None:
                print("\n" + "=" * 50)
                print(f"[DRY-RUN / CONSOLE] ({contest.platform.upper()}) Starts in {hours_left:.2f}h:")
                print("=" * 50)
                print(message)
                print("=" * 50 + "\n")
                notified_contests.append(contest)
            else:
                sent = send_notice_to_chats(bot, message, config.TELEGRAM_CHAT_IDS)
                if sent:
                    store.mark_notified(contest)
                    notified_contests.append(contest)

    return notified_contests


def run_scheduler_worker(bot, store: NotifiedStore, stop_event: threading.Event):
    """
    Background worker loop that periodically checks for contests.
    """
    logger.info(
        "Background scheduler started (interval: %d minutes, reminder window: %.1f hours).",
        config.CHECK_INTERVAL_MINUTES,
        config.REMINDER_HOURS_BEFORE,
    )

    # Initial check on startup
    try:
        check_and_notify(bot, store)
        store.prune_old()
    except Exception as e:
        logger.error("Error in initial scheduler check: %s", e)

    interval_seconds = config.CHECK_INTERVAL_MINUTES * 60

    while not stop_event.is_set():
        # Wait for the next interval or until stopped
        stopped = stop_event.wait(timeout=interval_seconds)
        if stopped:
            break

        try:
            logger.info("Running scheduled contest reminder check...")
            check_and_notify(bot, store)
            store.prune_old()
        except Exception as e:
            logger.error("Error during scheduled contest check: %s", e)

    logger.info("Background scheduler stopped.")
