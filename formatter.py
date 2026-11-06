"""
Message formatter for contest reminders matching DIU ACM format.
"""

from models import Contest


def format_contest_notice(contest: Contest) -> str:
    """
    Formats a contest reminder message in the exact required DIU ACM format:

    #contest_reminder #codeforces

    Codeforces Round 1132 (Div. 2)
    📅 Date: Friday, 6 November, 2026
    ⏰ Start Time: 8:35 PM
    ⏳ Duration: 02 hours 15 minutes
    🔗 Contest Link: https://codeforces.com/contests/2284

    ⚠️ Important Notice:

    Any kind of cheating or plagiarism will result in a permanent ban from DIU ACM.

    Best of luck to all participants.
    Happy coding 🖤
    """
    platform_tag = f"#{contest.platform.lower()}"
    header = f"#contest_reminder {platform_tag}"

    dt = contest.start_time

    # Date format: e.g. "Friday, 6 November, 2026"
    weekday = dt.strftime("%A")
    day = dt.day  # no leading zero
    month = dt.strftime("%B")
    year = dt.year
    date_str = f"{weekday}, {day} {month}, {year}"

    # Start Time format: e.g. "8:35 PM" (12-hour without leading zero on hour)
    hour = int(dt.strftime("%I"))
    minute = dt.strftime("%M")
    am_pm = dt.strftime("%p")
    time_str = f"{hour}:{minute} {am_pm}"

    # Duration format: e.g. "02 hours 15 minutes"
    hours, minutes = contest.duration_hours_minutes
    duration_str = f"{hours:02d} hours {minutes:02d} minutes"

    message = (
        f"{header}\n\n"
        f"{contest.name}\n"
        f"📅 Date: {date_str}\n"
        f"⏰ Start Time: {time_str}\n"
        f"⏳ Duration: {duration_str}\n"
        f"🔗 Contest Link: {contest.link}\n\n"
        f"⚠️ Important Notice:\n\n"
        f"Any kind of cheating or plagiarism will result in a permanent ban from DIU ACM.\n\n"
        f"Best of luck to all participants.\n"
        f"Happy coding 🖤"
    )

    return message
