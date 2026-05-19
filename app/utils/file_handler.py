"""
file_handler.py — Persistence helpers (pickle, CSV, JSON, logging).

All I/O is funnelled through this module so the rest of the codebase
never touches raw file operations directly.
"""

import csv
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.utils.config import (
    ATTENDANCE_FILE,
    CSV_COLUMNS,
    ENCODINGS_FILE,
    LOG_FILE,
    METADATA_FILE,
)


# ─── Logging Setup ─────────────────────────────────────────────────────────────

def setup_logger(name: str = "FaceAttendance") -> logging.Logger:
    """Configure and return the application-wide logger."""
    logger = logging.getLogger(name)
    if logger.handlers:          # Already initialised — return existing
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


logger = setup_logger()


# ─── Encoding Store ────────────────────────────────────────────────────────────

def save_encodings(data: Dict[str, Any]) -> None:
    """Persist face encodings dict to a pickle file."""
    ENCODINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)
    logger.info(f"Encodings saved → {ENCODINGS_FILE}  ({len(data.get('names', []))} entries)")


def load_encodings() -> Optional[Dict[str, Any]]:
    """Load face encodings from pickle. Returns None if file missing."""
    if not ENCODINGS_FILE.exists():
        logger.warning("Encodings file not found. Register users first.")
        return None
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    logger.info(f"Loaded {len(data.get('names', []))} face encodings.")
    return data


# ─── User Metadata ─────────────────────────────────────────────────────────────

def save_metadata(metadata: Dict[str, Any]) -> None:
    """Save user metadata (name, roll, dept …) as JSON."""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def load_metadata() -> Dict[str, Any]:
    """Load user metadata; returns empty dict if missing."""
    if not METADATA_FILE.exists():
        return {}
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Attendance CSV ────────────────────────────────────────────────────────────

def ensure_attendance_csv() -> None:
    """Create the attendance CSV with headers if it doesn't exist."""
    ATTENDANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ATTENDANCE_FILE.exists():
        with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
        logger.info(f"Attendance CSV created → {ATTENDANCE_FILE}")


def append_attendance_record(name: str, status: str = "Present") -> None:
    """Append a single attendance record with current timestamp."""
    ensure_attendance_csv()
    now = datetime.now()
    record = {
        "Name": name,
        "Date": now.strftime("%Y-%m-%d"),
        "Time": now.strftime("%H:%M:%S"),
        "Status": status,
    }
    with open(ATTENDANCE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(record)
    logger.info(f"Attendance marked → {record}")


def read_attendance_records() -> List[Dict[str, str]]:
    """Return all rows from the attendance CSV as a list of dicts."""
    ensure_attendance_csv()
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_todays_attendees() -> List[str]:
    """Return names already marked present today (for duplicate prevention)."""
    today = datetime.now().strftime("%Y-%m-%d")
    records = read_attendance_records()
    return [r["Name"] for r in records if r.get("Date") == today]


def get_attendance_summary() -> Dict[str, int]:
    """Count total attendance entries per person (all-time)."""
    records = read_attendance_records()
    summary: Dict[str, int] = {}
    for r in records:
        name = r.get("Name", "Unknown")
        summary[name] = summary.get(name, 0) + 1
    return summary
