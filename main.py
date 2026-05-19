"""
main.py — Application Entry Point

Run with:  python main.py
"""

import sys
import tkinter as tk
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ui.main_ui import FaceAttendanceApp
from app.utils.file_handler import setup_logger

logger = setup_logger()


def main() -> None:
    logger.info("═" * 60)
    logger.info("  Face Recognition Attendance System — Starting Up")
    logger.info("═" * 60)

    root = tk.Tk()

    try:
        # High-DPI awareness on Windows
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = FaceAttendanceApp(root)
    root.mainloop()

    logger.info("Application exited cleanly.")


if __name__ == "__main__":
    main()
