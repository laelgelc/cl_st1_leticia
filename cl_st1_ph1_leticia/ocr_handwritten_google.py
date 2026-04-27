"""
Handwritten OCR using Google Cloud Vision.

This script:
- Loads environment variables from env/.env (including GOOGLE_APPLICATION_CREDENTIALS).
- Uses Google Cloud Vision's DOCUMENT_TEXT_DETECTION to perform OCR, suitable for
  handwritten or dense text images.
- Accepts the image path as a command-line argument.
- Prints the recognized text to the console.
- Saves the recognized text to a .txt file next to the image
  (e.g., docs/image.jpeg -> docs/image.txt).

Usage (from the project root):

    python ocr_handwritten_google.py PATH/TO/IMAGE [--lang LANG_CODE]

Examples:

    python ocr_handwritten_google.py docs/WhatsApp_Image_2026-04-27_at_11.37.16.jpeg
    python ocr_handwritten_google.py docs/notes.jpeg --lang pt

Requirements:
- A Google Cloud project with the Vision API enabled.
- A service account JSON key whose path is set in GOOGLE_APPLICATION_CREDENTIALS.
- An env/.env file containing, for example:
    GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/your-key.json
"""

import argparse
import io
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import vision


def load_env():
    """
    Load environment variables from env/.env (relative to this script).
    """
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir / "env" / ".env"

    if env_path.is_file():
        load_dotenv(env_path)
    else:
        print(f"Warning: .env file not found at {env_path}")


def ocr_image(image_path: Path, language_hint: str = "pt") -> str:
    """
    Run Google Vision DOCUMENT_TEXT_DETECTION on the given image.
    """
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(
        image=image,
        image_context=vision.ImageContext(
            language_hints=[language_hint]
        ),
    )

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    return response.full_text_annotation.text


def save_text(next_to_image: Path, text: str) -> Path:
    """
    Save OCR text as a .txt file next to the image.
    E.g. docs/img.jpeg -> docs/img.txt
    """
    txt_path = next_to_image.with_suffix(".txt")
    txt_path.write_text(text, encoding="utf-8")
    return txt_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Google Vision OCR on a handwritten image."
    )
    parser.add_argument(
        "image_path",
        help=(
            "Path to the image file "
            "(e.g. docs/WhatsApp_Image_2026-04-27_at_11.37.16.jpeg)"
        ),
    )
    parser.add_argument(
        "--lang",
        default="pt",
        help="Language hint for OCR (default: pt for Portuguese).",
    )
    return parser.parse_args()


def main():
    load_env()

    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        raise EnvironmentError(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. "
            "Define it in env/.env or export it in your shell."
        )

    args = parse_args()
    image_path = Path(args.image_path)

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    text = ocr_image(image_path, language_hint=args.lang)

    print("=== OCR RESULT ===")
    print(text)

    txt_path = save_text(image_path, text)
    print(f"\nSaved OCR text to: {txt_path}")


if __name__ == "__main__":
    main()