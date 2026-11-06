"""
Unit tests for ACM Contest Reminder Bot.
"""

import unittest
import datetime
import tempfile
import zoneinfo
from pathlib import Path

from models import Contest
from formatter import format_contest_notice
from storage import NotifiedStore
from scheduler import check_and_notify


class TestContestReminderBot(unittest.TestCase):
    def setUp(self):
        self.tz = zoneinfo.ZoneInfo("Asia/Dhaka")

    def test_codeforces_exact_format(self):
        # 1793975700 corresponds to Friday, 6 November, 2026, 8:35 PM BST
        start_dt = datetime.datetime.fromtimestamp(1793975700, tz=self.tz)
        contest = Contest(
            platform="codeforces",
            id="2284",
            name="Codeforces Round 1132 (Div. 2)",
            start_time=start_dt,
            duration_seconds=8100,  # 2 hours 15 min
            link="https://codeforces.com/contests/2284",
        )

        expected = (
            "#contest_reminder #codeforces\n\n"
            "Codeforces Round 1132 (Div. 2)\n"
            "📅 Date: Friday, 6 November, 2026\n"
            "⏰ Start Time: 8:35 PM\n"
            "⏳ Duration: 02 hours 15 minutes\n"
            "🔗 Contest Link: https://codeforces.com/contests/2284\n\n"
            "⚠️ Important Notice:\n\n"
            "Any kind of cheating or plagiarism will result in a permanent ban from DIU ACM.\n\n"
            "Best of luck to all participants.\n"
            "Happy coding 🖤"
        )

        formatted = format_contest_notice(contest)
        self.assertEqual(formatted, expected)

    def test_atcoder_exact_format(self):
        # 2026-11-07 21:00:00+0900 -> 2026-11-07 18:00:00+06:00
        start_dt = datetime.datetime(2026, 11, 7, 18, 0, tzinfo=self.tz)
        contest = Contest(
            platform="atcoder",
            id="abc483",
            name="AtCoder Beginner Contest 483",
            start_time=start_dt,
            duration_seconds=6000,  # 1 hour 40 min
            link="https://atcoder.jp/contests/abc483",
        )

        expected = (
            "#contest_reminder #atcoder\n\n"
            "AtCoder Beginner Contest 483\n"
            "📅 Date: Saturday, 7 November, 2026\n"
            "⏰ Start Time: 6:00 PM\n"
            "⏳ Duration: 01 hours 40 minutes\n"
            "🔗 Contest Link: https://atcoder.jp/contests/abc483\n\n"
            "⚠️ Important Notice:\n\n"
            "Any kind of cheating or plagiarism will result in a permanent ban from DIU ACM.\n\n"
            "Best of luck to all participants.\n"
            "Happy coding 🖤"
        )

        formatted = format_contest_notice(contest)
        self.assertEqual(formatted, expected)

    def test_storage_deduplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_file = Path(tmpdir) / "test_store.json"
            store = NotifiedStore(filepath=store_file)

            contest = Contest(
                platform="codeforces",
                id="9999",
                name="Test Round",
                start_time=datetime.datetime.now(self.tz),
                duration_seconds=7200,
                link="https://codeforces.com/contests/9999",
            )

            self.assertFalse(store.is_notified(contest))
            store.mark_notified(contest)
            self.assertTrue(store.is_notified(contest))

            # Test reload from file
            store2 = NotifiedStore(filepath=store_file)
            self.assertTrue(store2.is_notified(contest))
            self.assertEqual(store2.get_notified_count(), 1)


if __name__ == "__main__":
    unittest.main()
