"""
Storage manager to prevent sending duplicate contest reminders.
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from models import Contest
import config

logger = logging.getLogger(__name__)


class NotifiedStore:
    def __init__(self, filepath: Path = config.STORAGE_FILE):
        self.filepath = Path(filepath)
        self._lock = threading.Lock()
        self._data: dict = {}
        self._load()

    def _load(self):
        with self._lock:
            if not self.filepath.exists():
                self._data = {}
                return
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                logger.error("Failed to load notified contests storage: %s", e)
                self._data = {}

    def _save(self):
        """Atomic write to prevent file corruption."""
        tmp_path = self.filepath.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            logger.error("Failed to save notified contests storage: %s", e)
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def is_notified(self, contest: Contest) -> bool:
        """Returns True if reminder has already been sent for this contest."""
        with self._lock:
            return contest.unique_key in self._data

    def mark_notified(self, contest: Contest):
        """Marks a contest as notified and persists to storage."""
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            self._data[contest.unique_key] = {
                "platform": contest.platform,
                "contest_id": contest.id,
                "name": contest.name,
                "start_time": contest.start_time.isoformat(),
                "notified_at": now_iso,
            }
            self._save()

    def get_notified_count(self) -> int:
        with self._lock:
            return len(self._data)

    def prune_old(self, max_days: int = 14):
        """Removes entries older than max_days."""
        with self._lock:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
            keys_to_remove = []
            for key, entry in self._data.items():
                notified_str = entry.get("notified_at")
                if notified_str:
                    try:
                        notified_dt = datetime.fromisoformat(notified_str)
                        if notified_dt < cutoff:
                            keys_to_remove.append(key)
                    except Exception:
                        pass
            if keys_to_remove:
                for k in keys_to_remove:
                    del self._data[k]
                self._save()
                logger.info("Pruned %d expired entries from storage.", len(keys_to_remove))
