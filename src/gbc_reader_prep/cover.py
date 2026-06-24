"""Cover image extraction for the GBC Reader preprocessor.

GBCR-A6: pull the first page of the PDF as an image, downscale to the
display resolution (400x240), apply 1-bit Floyd-Steinberg dithering, and
make it available both as a saved PNG (for inspection) and as base64
(for embedding in the .book file by A-8).

Refs: A-6
"""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path

import pymupdf
from PIL import Image

logger = logging.getLogger(__name__)

COVER_WIDTH = 400
COVER_HEIGHT = 240

# Render at a higher resolution than the target before downscaling, so the
# dithering has real detail to work with instead of upscaled blur.
_RENDER_ZOOM = 2.0


def render_cover(pdf_path: Path | str) -> Image.Image:
    """Render the first page of a PDF as a 1-bit dithered cover image.

    Args:
        pdf_path: Path to the input PDF.

    Returns:
        A Pillow Image in mode "1" (1-bit), sized COVER_WIDTH x COVER_HEIGHT.

    Raises:
        FileNotFoundError: If pdf_path does not exist.
        Exception: PyMuPDF errors (e.g. corrupt or unsupported file) are
            allowed to propagate so the caller can surface them.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info("Rendering cover from first page of: %s", pdf_path)
    doc = pymupdf.open(pdf_path)
    try:
        if doc.page_count == 0:
            raise ValueError(f"PDF has no pages: {pdf_path}")

        page = doc[0]
        matrix = pymupdf.Matrix(_RENDER_ZOOM, _RENDER_ZOOM)
        pixmap = page.get_pixmap(matrix=matrix)
        image = Image.frombytes(
            "RGB", (pixmap.width, pixmap.height), pixmap.samples
        )
    finally:
        doc.close()

    image = image.convert("L").resize(
        (COVER_WIDTH, COVER_HEIGHT), Image.LANCZOS
    )
    # Pillow's default conversion to mode "1" applies Floyd-Steinberg
    # dithering.
    dithered = image.convert("1")
    return dithered


def cover_to_base64(image: Image.Image) -> str:
    """Encode a Pillow Image as a base64 PNG string."""
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def extract_cover(pdf_path: Path | str, out_dir: Path | str) -> tuple[Path, str]:
    """Extract the cover image, save it to out_dir, and base64-encode it.

    Args:
        pdf_path: Path to the input PDF.
        out_dir: Directory to save the cover PNG into. Created if missing.

    Returns:
        A tuple of (path to the saved cover.png, base64-encoded PNG string).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    image = render_cover(pdf_path)
    cover_path = out_dir / "cover.png"
    image.save(cover_path, format="PNG")
    logger.info("Saved cover image to %s", cover_path)

    return cover_path, cover_to_base64(image)
