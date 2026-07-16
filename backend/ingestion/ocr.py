"""
OCR Engine
----------
Wraps pytesseract (Tesseract OCR) for scanned PDFs / images / P&ID
screenshots. Falls back gracefully with a clear message if the Tesseract
binary isn't installed on the host, rather than crashing ingestion.
"""
from __future__ import annotations

import io
import logging
from PIL import Image

logger = logging.getLogger("ocr")

_TESSERACT_AVAILABLE = None


def _check_tesseract() -> bool:
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
    except Exception:
        _TESSERACT_AVAILABLE = False
    return _TESSERACT_AVAILABLE


def ocr_image_bytes(image_bytes: bytes) -> str:
    """Run OCR on raw image bytes and return extracted text."""
    if not _check_tesseract():
        return "[OCR unavailable: Tesseract binary not installed on this host. " \
               "Install with `sudo apt-get install tesseract-ocr` to enable scanned " \
               "document / P&ID text extraction.]"
    import pytesseract
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""


def ocr_image_path(path: str) -> str:
    with open(path, "rb") as f:
        return ocr_image_bytes(f.read())
