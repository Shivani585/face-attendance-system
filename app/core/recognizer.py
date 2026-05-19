"""
recognizer.py — Processing Layer: Face Recognition

Matches live face encodings against the known database using
Euclidean distance and returns labels + confidence scores.
"""

import numpy as np
import face_recognition
from typing import List, Tuple

from app.utils.config import TOLERANCE
from app.utils.file_handler import setup_logger

logger = setup_logger()


class FaceRecognizer:
    """
    Compares a list of live encodings against a stored database.

    Euclidean distance in 128-d space:
      distance = 0   → perfect match
      distance < 0.5 → confident match (configurable via TOLERANCE)
      distance > 0.6 → likely different person
    """

    def __init__(self, tolerance: float = TOLERANCE):
        self.tolerance = tolerance
        logger.info(f"FaceRecognizer initialised  [tolerance={tolerance}]")

    # ── Public API ─────────────────────────────────────────────────────────────

    def identify(
        self,
        live_encodings: List[np.ndarray],
        known_encodings: List[np.ndarray],
        known_names: List[str],
    ) -> List[Tuple[str, float]]:
        """
        For each live encoding return (name, confidence) tuple.

        Confidence is derived from:
            confidence = 1 - (distance / tolerance)
        clipped to [0, 1].

        Parameters
        ----------
        live_encodings  : encodings from the current video frame
        known_encodings : database encodings
        known_names     : corresponding names

        Returns
        -------
        list of (name, confidence) — same length as live_encodings
        """
        results = []

        if not known_encodings:
            # No registered users — mark all as Unknown
            return [("Unknown", 0.0) for _ in live_encodings]

        for live_enc in live_encodings:
            name, conf = self._match_single(live_enc, known_encodings, known_names)
            results.append((name, conf))

        return results

    # ── Private ────────────────────────────────────────────────────────────────

    def _match_single(
        self,
        live_enc: np.ndarray,
        known_encodings: List[np.ndarray],
        known_names: List[str],
    ) -> Tuple[str, float]:
        """Find the best matching name for one live encoding."""
        distances = face_recognition.face_distance(known_encodings, live_enc)

        if len(distances) == 0:
            return ("Unknown", 0.0)

        best_idx  = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist <= self.tolerance:
            confidence = float(np.clip(1.0 - best_dist / self.tolerance, 0.0, 1.0))
            return (known_names[best_idx], round(confidence, 3))

        return ("Unknown", 0.0)

    def bulk_match_flags(
        self,
        live_encodings: List[np.ndarray],
        known_encodings: List[np.ndarray],
    ) -> List[bool]:
        """
        Quick boolean check — did we find ANY match for each encoding?
        Useful for real-time overlay decisions.
        """
        if not known_encodings:
            return [False] * len(live_encodings)
        return [
            any(face_recognition.compare_faces(known_encodings, enc, tolerance=self.tolerance))
            for enc in live_encodings
        ]
