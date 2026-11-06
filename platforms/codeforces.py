"""
Codeforces contest fetcher using Codeforces API.
"""

import logging
import datetime
import requests
from models import Contest
import config

logger = logging.getLogger(__name__)

CF_API_URL = "https://codeforces.com/api/contest.list?gym=false"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ACM-Contest-Bot/1.0",
    "Accept": "application/json",
}


def fetch_codeforces_contests() -> list[Contest]:
    """
    Fetches upcoming contests from Codeforces API.
    Returns a list of Contest objects sorted by start time ascending.
    """
    contests: list[Contest] = []
    try:
        response = requests.get(CF_API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            logger.warning("Codeforces API returned non-OK status: %s", data.get("comment"))
            return []

        for item in data.get("result", []):
            if item.get("phase") != "BEFORE":
                continue

            start_epoch = item.get("startTimeSeconds")
            if not start_epoch:
                continue

            contest_id = str(item.get("id"))
            name = str(item.get("name", "Codeforces Round")).strip()
            duration_seconds = int(item.get("durationSeconds", 7200))

            start_time = datetime.datetime.fromtimestamp(start_epoch, tz=config.TZ)
            link = f"https://codeforces.com/contests/{contest_id}"

            contest = Contest(
                platform="codeforces",
                id=contest_id,
                name=name,
                start_time=start_time,
                duration_seconds=duration_seconds,
                link=link,
            )
            contests.append(contest)

        # Sort chronologically
        contests.sort(key=lambda c: c.start_time)

    except Exception as exc:
        logger.error("Error fetching Codeforces contests: %s", exc)

    return contests
