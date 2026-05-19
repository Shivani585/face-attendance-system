"""
scripts/register_faces.py — Batch Face Registration CLI

Use this script to register multiple users from image files
without needing to launch the full GUI.

Usage:
    python scripts/register_faces.py
    python scripts/register_faces.py --from-dir data/dataset
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.face_encoder import FaceEncoder
from app.utils.config import DATASET_DIR
from app.utils.file_handler import setup_logger

logger = setup_logger("RegisterFaces")

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def register_from_directory(directory: Path, encoder: FaceEncoder) -> None:
    """
    Scan `directory` for image files.
    Filename (without extension) is used as the person's name.
    Supports multiple images per person — averages are NOT taken;
    each image adds one encoding (ensemble matching).
    """
    images = [f for f in directory.iterdir() if f.suffix.lower() in SUPPORTED_EXTS]

    if not images:
        logger.warning(f"No images found in {directory}")
        return

    success, failed = 0, 0
    for img_path in sorted(images):
        name = img_path.stem.replace("_", " ").title()
        logger.info(f"Registering '{name}' from {img_path.name} …")
        ok = encoder.register_user(name, img_path)
        if ok:
            success += 1
            print(f"  ✔  {name}")
        else:
            failed += 1
            print(f"  ✘  {name} — no face detected")

    print(f"\nRegistration complete:  {success} added,  {failed} failed.")


def interactive_register(encoder: FaceEncoder) -> None:
    """Simple interactive loop for manual registration."""
    print("\n── Interactive Face Registration ─────────────────")
    print("Type 'quit' to exit.\n")

    while True:
        name = input("Enter person's name: ").strip()
        if name.lower() == "quit":
            break
        if not name:
            continue

        path_str = input(f"Enter image path for {name}: ").strip()
        img_path = Path(path_str)

        if not img_path.exists():
            print(f"  ✘  File not found: {img_path}")
            continue

        ok = encoder.register_user(name, img_path)
        print(f"  {'✔' if ok else '✘'}  {name}")

    print(f"\nTotal registered: {encoder.user_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register faces for the attendance system.")
    parser.add_argument(
        "--from-dir",
        type=Path,
        default=None,
        help="Path to directory of images (filename = name).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for name + image path one by one.",
    )
    args = parser.parse_args()

    encoder = FaceEncoder()
    print(f"\nCurrent registrations: {encoder.user_count}")

    if args.from_dir:
        register_from_directory(args.from_dir, encoder)
    elif args.interactive:
        interactive_register(encoder)
    else:
        # Default: scan the standard dataset directory
        print(f"\nScanning default dataset directory: {DATASET_DIR}")
        register_from_directory(DATASET_DIR, encoder)


if __name__ == "__main__":
    main()
