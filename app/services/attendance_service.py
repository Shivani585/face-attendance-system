"""
attendance_service.py — Application Layer: Attendance Manager

Decides WHEN to mark attendance (cooldown, daily-once logic) and
delegates persistence to file_handler.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from app.utils.file_handler import (
    append_attendance_record,
    get_todays_attendees,
    read_attendance_records,
    get_attendance_summary,
    setup_logger,
)
from app.utils.config import ATTENDANCE_COOLDOWN_SECS

logger = setup_logger()


class AttendanceService:
    """
    Central attendance logic with in-memory cooldown tracking.

    Rules
    -----
    1. A person is only marked once per calendar day.
    2. After an attempted mark, a cooldown prevents repeated log spam.
    3. All writes are delegated to file_handler (single responsibility).
    """

    def __init__(self, cooldown_secs: int = ATTENDANCE_COOLDOWN_SECS):
        self.cooldown_secs = cooldown_secs
        # name → epoch timestamp of last mark attempt
        self._last_seen: Dict[str, float] = {}
        # Refresh from disk so we survive hot-reloads
        self._todays_marked: List[str] = get_todays_attendees()
        logger.info(
            f"AttendanceService ready.  Already marked today: {self._todays_marked}"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def try_mark(self, name: str) -> str:
        """
        Attempt to mark attendance for `name`.

        Returns
        -------
        "marked"         — freshly logged
        "already_marked" — already present today
        "cooldown"       — within cooldown window
        "unknown"        — face not recognised
        """
        if name == "Unknown":
            return "unknown"

        now = time.time()

        # Cooldown check
        if name in self._last_seen:
            elapsed = now - self._last_seen[name]
            if elapsed < self.cooldown_secs:
                return "cooldown"

        self._last_seen[name] = now

        # Daily-once check
        if name in self._todays_marked:
            return "already_marked"

        # Mark it!
        append_attendance_record(name, status="Present")
        self._todays_marked.append(name)
        logger.info(f"✔ Attendance marked: {name}")
        return "marked"

    def get_all_records(self) -> List[Dict]:
        return read_attendance_records()

    def get_todays_records(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        return [r for r in self.get_all_records() if r.get("Date") == today]

    def get_summary(self) -> Dict[str, int]:
        return get_attendance_summary()

    def is_marked_today(self, name: str) -> bool:
        return name in self._todays_marked

    def refresh(self) -> None:
        """Re-sync in-memory state from CSV (call after manual edits)."""
        self._todays_marked = get_todays_attendees()
