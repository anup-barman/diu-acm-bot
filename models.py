"""
Data models for ACM Contest Reminder Bot.
"""

from dataclasses import dataclass
import datetime


@dataclass
class Contest:
    platform: str  # 'codeforces' or 'atcoder'
    id: str  # Contest ID/slug (e.g. '2284' or 'abc483')
    name: str  # Contest name (e.g. 'Codeforces Round 1132 (Div. 2)')
    start_time: datetime.datetime  # Timezone-aware datetime
    duration_seconds: int  # Duration in seconds
    link: str  # Link to the contest

    @property
    def unique_key(self) -> str:
        """Globally unique key across platforms."""
        return f"{self.platform.lower()}_{self.id}"

    def hours_until_start(self, now: datetime.datetime = None) -> float:
        """Returns the number of hours remaining until the contest starts."""
        if now is None:
            now = datetime.datetime.now(self.start_time.tzinfo)
        return (self.start_time - now).total_seconds() / 3600.0

    @property
    def duration_hours_minutes(self) -> tuple[int, int]:
        """Returns (hours, minutes) of contest duration."""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        return hours, minutes
