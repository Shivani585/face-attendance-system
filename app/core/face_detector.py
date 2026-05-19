"""
face_detector.py — Processing Layer: Face Detection

Wraps face_recognition's face detection so that the rest of the system
is decoupled from the underlying library choice.
"""

import cv2
import numpy as np
from typing import List, Tuple

import face_recognition

from app.utils.config import FRAME_SCALE, MODEL, UPSAMPLE_TIMES
from app.utils.file_handler import setup_logger

logger = setup_logger()


class FaceDetector:
    """
    Detects face bounding boxes in an image frame.

    Strategy:
      1. Downscale the raw frame for speed.
      2. Run face_recognition.face_locations (HOG or CNN model).
      3. Return locations scaled back to original dimensions.
    """

    def __init__(self, model: str = MODEL, scale: float = FRAME_SCALE):
        self.model  = model
        self.scale  = scale
        logger.info(f"FaceDetector initialised  [model={model}, scale={scale}]")

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect(self, frame_bgr: np.ndarray) -> Tuple[np.ndarray, List[Tuple]]:
        """
        Detect faces in a BGR OpenCV frame.

        Returns
        -------
        small_rgb : np.ndarray
            Downscaled RGB frame used for encoding (re-used by encoder).
        locations : list of (top, right, bottom, left)
            Face bounding boxes scaled to the *original* frame dimensions.
        """
        small_rgb = self._preprocess(frame_bgr)
        raw_locs  = face_recognition.face_locations(
            small_rgb,
            number_of_times_to_upsample=UPSAMPLE_TIMES,
            model=self.model,
        )
        scaled_locs = self._scale_up(raw_locs)
        return small_rgb, scaled_locs, raw_locs

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _preprocess(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Resize + convert BGR→RGB."""
        h, w = frame_bgr.shape[:2]
        small = cv2.resize(frame_bgr, (int(w * self.scale), int(h * self.scale)))
        return cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    def _scale_up(self, locations: List[Tuple]) -> List[Tuple]:
        """Map small-frame coordinates back to original frame size."""
        inv = 1.0 / self.scale
        return [
            (int(top * inv), int(right * inv), int(bottom * inv), int(left * inv))
            for top, right, bottom, left in locations
        ]

    @staticmethod
    def draw_boxes(
        frame_bgr: np.ndarray,
        locations: List[Tuple],
        labels: List[str],
        confidences: List[float],
        color_known=(0, 255, 128),
        color_unknown=(0, 80, 255),
    ) -> np.ndarray:
        """
        Draw bounding boxes + name tags + confidence bars on the frame.
        Returns an annotated copy (does NOT mutate the original).
        """
        out = frame_bgr.copy()
        for (top, right, bottom, left), label, conf in zip(locations, labels, confidences):
            is_known = label != "Unknown"
            box_color = color_known if is_known else color_unknown

            # --- Bounding rectangle with rounded-corner illusion via filled rects
            thickness = 2
            cv2.rectangle(out, (left, top), (right, bottom), box_color, thickness)

            # --- Filled tag background
            tag_h   = 28
            tag_top = bottom
            cv2.rectangle(out, (left - 1, tag_top), (right + 1, tag_top + tag_h), box_color, cv2.FILLED)

            # --- Name text
            conf_pct = f" {conf*100:.0f}%" if is_known else ""
            text     = f"  {label}{conf_pct}"
            cv2.putText(
                out, text,
                (left + 4, tag_top + 19),
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                (10, 10, 10),
                1,
                cv2.LINE_AA,
            )

            # --- Corner accent squares for a "HUD" feel
            s = 10
            for px, py in [(left, top), (right - s, top), (left, bottom - s), (right - s, bottom - s)]:
                cv2.rectangle(out, (px, py), (px + s, py + s), (255, 255, 255), -1)

        return out
