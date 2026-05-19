"""
config.py — Central configuration for Face Attendance System
All tunable constants live here; nothing is hard-coded elsewhere.
"""

import os
from pathlib import Path

# ─── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parents[2]
DATA_DIR       = BASE_DIR / "data"
DATASET_DIR    = DATA_DIR / "dataset"
ENCODINGS_DIR  = DATA_DIR / "encodings"
ATTENDANCE_DIR = DATA_DIR / "attendance"
LOGS_DIR       = BASE_DIR / "logs"

# Auto-create all directories on import
for _dir in (DATASET_DIR, ENCODINGS_DIR, ATTENDANCE_DIR, LOGS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ─── File Paths ────────────────────────────────────────────────────────────────
ENCODINGS_FILE   = ENCODINGS_DIR / "face_encodings.pkl"
METADATA_FILE    = ENCODINGS_DIR / "user_metadata.json"
ATTENDANCE_FILE  = ATTENDANCE_DIR / "attendance.csv"
LOG_FILE         = LOGS_DIR      / "system.log"

# ─── Camera Settings ──────────────────────────────────────────────────────────
CAMERA_INDEX       = 0          # Default webcam; change to 1 for external
FRAME_WIDTH        = 640
FRAME_HEIGHT       = 480
FRAME_SCALE        = 0.5        # Downscale factor for faster processing
PROCESS_EVERY_N    = 2          # Process every N-th frame (performance tuning)

# ─── Face Recognition Settings ────────────────────────────────────────────────
TOLERANCE          = 0.50       # Lower = stricter match (0.4–0.6 recommended)
MODEL              = "hog"      # "hog" (CPU-fast) | "cnn" (GPU-accurate)
NUM_JITTERS        = 1          # Encoding jitter passes; higher = more accurate
UPSAMPLE_TIMES     = 1          # How many times to upsample for small faces

# ─── Attendance Settings ──────────────────────────────────────────────────────
ATTENDANCE_COOLDOWN_SECS = 5    # Seconds before re-logging the same person
CSV_COLUMNS = ["Name", "Date", "Time", "Status"]

# ─── UI Settings ──────────────────────────────────────────────────────────────
UI_TITLE      = "Face Recognition Attendance System"
UI_THEME      = "dark"          # "dark" | "light"

# ─── Bounding Box Colours (BGR) ───────────────────────────────────────────────
COLOR_KNOWN   = (0, 255, 128)   # Neon green  — recognised face
COLOR_UNKNOWN = (0, 80, 255)    # Orange-red  — unknown face
COLOR_TEXT    = (255, 255, 255) # White text

# ─── Sound ─────────────────────────────────────────────────────────────────────
ENABLE_SOUND  = True            # Requires 'playsound' or system beep fallback
