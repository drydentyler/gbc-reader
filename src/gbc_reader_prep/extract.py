"""PDF text extraction for the GBC Reader preprocessor.

GBCR-A2: PDF text extraction proof-of-concept.

The narrowest possible use of PyMuPDF: open a PDF, read text from every
page in the default "text" mode, write it out with a form-feed page
separator. No layout reasoning, no chapter detection, no trimming, no
pagination. Those live in later tickets (A-3 onward).
"""
from __future__ import annotations

import logging
from pathlib import Path

import pymupdf

logger = logging.getLogger(__name__)

# Form feed (0x0C). Convention from the PyMuPDF docs example. Makes the
# output trivially splittable back into pages with `text.split(b"\x0c")`
# if any later debugging needs it.
PAGE_SEPARATOR = b"\x0c"


def extract_text_pages(pdf_path: Path | str) -> list[str]:
    """Extract text from every page of a PDF, returned as an in-memory list.

    Unlike :func:`extract_text`, this does no file I/O and applies no page
    separator — callers that need each page's text individually (e.g. the
    pagination engine in :mod:`gbc_reader_prep.paginate`) use this instead
    of re-parsing the form-feed-delimited ``.txt`` output.

    Args:
        pdf_path: Path to the input PDF.

    Returns:
        A list of per-page text, 0-indexed, in document order.

    Raises:
        FileNotFoundError: If pdf_path does not exist.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    try:
        return [page.get_text() for page in doc]
    finally:
        doc.close()


def extract_text(pdf_path: Path | str, out_path: Path | str) -> int:
    """Extract plain text from every page of a PDF into a UTF-8 .txt file.

    Args:
        pdf_path: Path to the input PDF.
        out_path: Path to the output .txt file. Parent directories will be
            created if missing. An existing file at this path will be
            overwritten.

    Returns:
        The number of pages written.

    Raises:
        FileNotFoundError: If pdf_path does not exist.
        Exception: PyMuPDF errors (e.g. corrupt or unsupported file) are
            allowed to propagate so the caller can surface them.
    """
    pdf_path = Path(pdf_path)
    out_path = Path(out_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Opening PDF: %s", pdf_path)
    doc = pymupdf.open(pdf_path)
    try:
        page_count = doc.page_count
        logger.info("PDF has %d page(s)", page_count)

        empty_pages = 0
        with open(out_path, "wb") as out:
            for page in doc:
                text = page.get_text()
                if not text.strip():
                    empty_pages += 1
                out.write(text.encode("utf-8"))
                out.write(PAGE_SEPARATOR)

        if empty_pages:
            logger.warning(
                "%d / %d page(s) produced no text. "
                "If this is a scanned PDF without OCR, that is expected; "
                "OCR support is out of scope for GBCR-A2.",
                empty_pages,
                page_count,
            )
        logger.info("Wrote %d page(s) of text to %s", page_count, out_path)
        return page_count
    finally:
        doc.close()
