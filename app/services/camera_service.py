"""
camera_service.py — Application Layer: Camera Feed Manager

Provides a thread-safe frame buffer so the UI thread can consume
frames without blocking the capture loop.
"""

import threading
import cv2
import numpy as np
from typing import Optional, Callable

from app.utils.config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT
from app.utils.file_handler import setup_logger

logger = setup_logger()


class CameraService:
    """
    Manages webcam capture in a background thread.

    Usage
    -----
    cam = CameraService()
    cam.start()
    frame = cam.get_frame()   # latest BGR frame, or None
    cam.stop()
    """

    def __init__(
        self,
        index: int = CAMERA_INDEX,
        width: int = FRAME_WIDTH,
        height: int = FRAME_HEIGHT,
    ):
        self.index   = index
        self.width   = width
        self.height  = height

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray]     = None
        self._lock   = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Optional callback: called with every captured frame
        self.on_frame: Optional[Callable[[np.ndarray], None]] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Open the camera and start the capture thread."""
        self._cap = cv2.VideoCapture(self.index)
        if not self._cap.isOpened():
            logger.error(f"Cannot open camera (index={self.index}).")
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._running = True
        self._thread  = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Camera started (index={self.index}, {self.width}×{self.height})")
        return True

    def stop(self) -> None:
        """Signal the capture thread to stop and release the camera."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
        if self._cap and self._cap.isOpened():
            self._cap.release()
        logger.info("Camera stopped.")

    # ── Frame Access ───────────────────────────────────────────────────────────

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the most recently captured frame (BGR), thread-safe."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Private ────────────────────────────────────────────────────────────────

    def _capture_loop(self) -> None:
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                break
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera.")
                continue
            with self._lock:
                self._frame = frame
            if self.on_frame:
                self.on_frame(frame)
        logger.debug("Capture loop exited.")
