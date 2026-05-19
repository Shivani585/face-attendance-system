"""
face_encoder.py — Processing Layer: Face Encoding

Converts detected face regions to 128-dimensional embedding vectors
using dlib's ResNet model (via face_recognition).
"""

import numpy as np
from pathlib import Path
from typing import List, Optional

import cv2
import face_recognition

from app.utils.config import NUM_JITTERS
from app.utils.file_handler import setup_logger, save_encodings, load_encodings

logger = setup_logger()


class FaceEncoder:
    """
    Generates and manages 128-d face embeddings.

    The encoding database is a dict:
      {
        "names":     [str, ...],
        "encodings": [np.ndarray shape (128,), ...]
      }
    """

    def __init__(self):
        self._db = {"names": [], "encodings": []}
        self._load()

    # ── Public API ─────────────────────────────────────────────────────────────

    def encode_faces(
        self,
        rgb_frame: np.ndarray,
        locations: List,
    ) -> List[np.ndarray]:
        """
        Return 128-d encodings for each face location in `rgb_frame`.

        Parameters
        ----------
        rgb_frame : RGB image (already downscaled by FaceDetector)
        locations : raw (small-frame) face_locations list
        """
        return face_recognition.face_encodings(
            rgb_frame,
            known_face_locations=locations,
            num_jitters=NUM_JITTERS,
        )

    def encode_image_file(self, image_path: Path) -> Optional[np.ndarray]:
        """
        Encode the first face found in an image file.
        Returns None if no face is detected.
        """
        img = face_recognition.load_image_file(str(image_path))
        locs = face_recognition.face_locations(img)
        if not locs:
            logger.warning(f"No face detected in {image_path.name}")
            return None
        enc = face_recognition.face_encodings(img, known_face_locations=locs, num_jitters=NUM_JITTERS)
        return enc[0] if enc else None

    def register_user(self, name: str, image_path: Path) -> bool:
        """
        Add a user's face encoding to the in-memory DB and persist.
        Returns True on success.
        """
        enc = self.encode_image_file(image_path)
        if enc is None:
            return False
        self._db["names"].append(name)
        self._db["encodings"].append(enc)
        save_encodings(self._db)
        logger.info(f"User registered: {name}")
        return True

    def register_from_webcam(self, name: str, frame_bgr: np.ndarray) -> bool:
        """
        Register a user from a live webcam frame.
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        if not locs:
            logger.warning("register_from_webcam: no face detected in frame.")
            return False
        encs = face_recognition.face_encodings(rgb, locs, num_jitters=NUM_JITTERS)
        if not encs:
            return False
        self._db["names"].append(name)
        self._db["encodings"].append(encs[0])
        save_encodings(self._db)
        logger.info(f"User registered from webcam: {name}")
        return True

    def reload(self) -> None:
        """Hot-reload encodings from disk (useful after new registrations)."""
        self._load()

    @property
    def known_names(self) -> List[str]:
        return self._db["names"]

    @property
    def known_encodings(self) -> List[np.ndarray]:
        return self._db["encodings"]

    @property
    def user_count(self) -> int:
        return len(self._db["names"])

    # ── Private ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        data = load_encodings()
        if data:
            self._db = data
