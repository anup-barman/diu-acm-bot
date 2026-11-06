"""
AtCoder contest fetcher scraping https://atcoder.jp/contests/
"""

import logging
import datetime
import zoneinfo
import requests
from bs4 import BeautifulSoup
from models import Contest
import config

logger = logging.getLogger(__name__)

ATCODER_CONTESTS_URL = "https://atcoder.jp/contests/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 ACM-Contest-Bot/1.0"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def parse_atcoder_datetime(raw_str: str) -> datetime.datetime:
    """
    Parses AtCoder start time string (e.g. '2026-11-07 21:00:00+0900')
    and converts it into the configured application timezone.
    """
    raw_str = raw_str.strip()
    try:
        dt_with_tz = datetime.datetime.strptime(raw_str, "%Y-%m-%d %H:%M:%S%z")
        return dt_with_tz.astimezone(config.TZ)
    except ValueError:
        pass

    try:
        # Fallback assuming JST (UTC+9)
        jst = zoneinfo.ZoneInfo("Asia/Tokyo")
        dt_naive = datetime.datetime.strptime(raw_str, "%Y-%m-%d %H:%M:%S")
        dt_jst = dt_naive.replace(tzinfo=jst)
        return dt_jst.astimezone(config.TZ)
    except ValueError:
        pass

    # Generic ISO fallback
    dt_iso = datetime.datetime.fromisoformat(raw_str)
    if dt_iso.tzinfo is None:
        dt_iso = dt_iso.replace(tzinfo=zoneinfo.ZoneInfo("Asia/Tokyo"))
    return dt_iso.astimezone(config.TZ)


def parse_duration_to_seconds(duration_str: str) -> int:
    """
    Parses duration string in format 'HH:MM' (e.g. '01:40' or '100:00') into seconds.
    """
    duration_str = duration_str.strip()
    try:
        parts = duration_str.split(":")
        if len(parts) == 2:
            hours, minutes = int(parts[0]), int(parts[1])
            return hours * 3600 + minutes * 60
        elif len(parts) == 3:
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except Exception:
        pass
    return 0


def fetch_atcoder_contests() -> list[Contest]:
    """
    Scrapes upcoming contests from AtCoder.
    Returns a list of Contest objects sorted by start time ascending.
    """
    contests: list[Contest] = []
    try:
        response = requests.get(ATCODER_CONTESTS_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        upcoming_div = soup.find("div", id="contest-table-upcoming")
        if not upcoming_div:
            logger.info("No upcoming contests section found on AtCoder.")
            return []

        rows = upcoming_div.find_all("tr")
        for row in rows[1:]:  # skip header
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            # Start time in column 0
            time_tag = cols[0].find("time")
            raw_time = time_tag.text.strip() if time_tag else cols[0].text.strip()
            if not raw_time:
                continue

            try:
                start_time = parse_atcoder_datetime(raw_time)
            except Exception as e:
                logger.warning("Failed to parse AtCoder start time '%s': %s", raw_time, e)
                continue

            # Contest Name and URL in column 1
            link_tag = cols[1].find("a")
            if not link_tag:
                continue

            contest_name = link_tag.text.strip()
            href = link_tag.get("href", "").strip()
            contest_id = href.strip("/").split("/")[-1]

            if href.startswith("/"):
                link = f"https://atcoder.jp{href}"
            elif href.startswith("http"):
                link = href
            else:
                link = f"https://atcoder.jp/contests/{contest_id}"

            # Duration in column 2
            raw_duration = cols[2].text.strip()
            duration_seconds = parse_duration_to_seconds(raw_duration)

            contest = Contest(
                platform="atcoder",
                id=contest_id,
                name=contest_name,
                start_time=start_time,
                duration_seconds=duration_seconds,
                link=link,
            )
            contests.append(contest)

        contests.sort(key=lambda c: c.start_time)

    except Exception as exc:
        logger.error("Error scraping AtCoder contests: %s", exc)

    return contests
