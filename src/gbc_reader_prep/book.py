"""``.book`` file writer.

Ticket: A-8 — assemble the manifest, chapters, pages, and cover produced
by earlier tickets (A-3/A-4 chapter detection, A-5 trimming, A-6 cover
extraction, A-7 pagination) into a single JSON ``.book`` file, per the
schema in the project plan (`GBC_Reader_Project_Plan.md` §3.1).

Framework-agnostic — no argparse, no CLI concerns. ``preprocess.py``
calls :func:`write_book_path` when ``--output`` ends in ``.book``.

Refs: A-8
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .chapters import Chapter, detect_chapters_path
from .cover import cover_to_base64, render_cover
from .extract import extract_text_pages
from .paginate import (
    DEFAULT_FONT_METRICS,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    FontMetrics,
    Page,
    paginate_chapters,
)
from .trim import detect_content_bounds

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def _relevant_chapters(
    chapters: list[Chapter], start_page: int, end_page: int
) -> list[Chapter]:
    """Return the in-range, ``start_page``-sorted chapter subset that
    :func:`gbc_reader_prep.paginate.paginate_chapters` lays out, with the
    same single blank-title fallback when none fall in range.

    ``Page.chapter_id`` indexes into this exact list — keep this in sync
    with ``paginate_chapters``'s own internal subset selection.
    """
    relevant = sorted(
        (c for c in chapters if start_page <= c.start_page <= end_page),
        key=lambda c: c.start_page,
    )
    if not relevant:
        relevant = [Chapter(title="", start_page=start_page, level=1)]
    return relevant


def _read_metadata(pdf_path: Path) -> tuple[str, str]:
    """Read ``title``/``author`` from PDF metadata, falling back to the
    filename stem / an empty string when metadata is missing or blank."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    try:
        meta = doc.metadata or {}
    finally:
        doc.close()

    title = (meta.get("title") or "").strip() or pdf_path.stem
    author = (meta.get("author") or "").strip()
    return title, author


def build_book(
    pdf_path: Path | str,
    *,
    title: str | None = None,
    author: str | None = None,
    font_metrics: FontMetrics = DEFAULT_FONT_METRICS,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
    start_page: int | None = None,
    end_page: int | None = None,
    include_cover: bool = True,
) -> dict[str, Any]:
    """Assemble a ``.book`` manifest dict for ``pdf_path``.

    Runs chapter detection, content-bounds trimming (unless overridden),
    pagination, and (unless disabled) cover extraction, then combines
    them into the JSON-serializable manifest described in the project
    plan.

    Args:
        pdf_path: Path to the input PDF.
        title: Book title. Defaults to the PDF's metadata title, falling
            back to the filename stem if blank.
        author: Book author. Defaults to the PDF's metadata author
            (empty string if blank/absent).
        font_metrics: Character grid for pagination. Defaults to
            :data:`gbc_reader_prep.paginate.DEFAULT_FONT_METRICS`.
        display_width: Display width in pixels. Defaults to 400.
        display_height: Display height in pixels. Defaults to 240.
        start_page: Override for the main-content start page (0-indexed).
            Auto-detected via :mod:`gbc_reader_prep.trim` if omitted.
        end_page: Override for the main-content end page (0-indexed,
            inclusive). Auto-detected via :mod:`gbc_reader_prep.trim` if
            omitted.
        include_cover: If ``True`` (default), render and embed the cover
            image as base64 in ``cover_png_base64``. If ``False``, that
            field is ``None`` and no cover render is performed.

    Returns:
        A dict matching the ``.book`` schema (``schema_version``,
        ``title``, ``author``, ``display``, ``cover_png_base64``,
        ``chapters``, ``pages``, ``total_pages``).

    Raises:
        FileNotFoundError: If ``pdf_path`` does not exist.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    detected_title, detected_author = _read_metadata(pdf_path)
    title = title if title is not None else detected_title
    author = author if author is not None else detected_author

    chapters = detect_chapters_path(pdf_path)
    page_texts = extract_text_pages(pdf_path)

    if start_page is None or end_page is None:
        bounds = detect_content_bounds(chapters, len(page_texts))
        if start_page is None:
            start_page = bounds.start_page
        if end_page is None:
            end_page = bounds.end_page

    pages = paginate_chapters(
        page_texts,
        chapters,
        font_metrics=font_metrics,
        display_width=display_width,
        display_height=display_height,
        start_page=start_page,
        end_page=end_page,
    )
    relevant = _relevant_chapters(chapters, start_page, end_page)

    cover_base64 = None
    if include_cover:
        cover_base64 = cover_to_base64(render_cover(pdf_path))

    return {
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "author": author,
        "display": {
            "width_px": display_width,
            "height_px": display_height,
            "font": f"{font_metrics.char_width_px}x{font_metrics.line_height_px}",
        },
        "cover_png_base64": cover_base64,
        "chapters": [
            {"id": chapter_id, "title": chapter.title, "start_page": chapter.start_page}
            for chapter_id, chapter in enumerate(relevant)
        ],
        "pages": [
            {"chapter_id": page.chapter_id, "lines": page.lines} for page in pages
        ],
        "total_pages": len(pages),
    }


def write_book_path(
    pdf_path: Path | str,
    out_path: Path | str,
    **build_kwargs: Any,
) -> dict[str, Any]:
    """Build a ``.book`` manifest for ``pdf_path`` and write it as JSON to
    ``out_path``.

    Args:
        pdf_path: Path to the input PDF.
        out_path: Path to write the ``.book`` JSON file to. Parent
            directories are created if missing; an existing file is
            overwritten.
        **build_kwargs: Forwarded to :func:`build_book`.

    Returns:
        The manifest dict that was written (see :func:`build_book`).

    Raises:
        FileNotFoundError: If ``pdf_path`` does not exist.
    """
    out_path = Path(out_path)
    book = build_book(pdf_path, **build_kwargs)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(book), encoding="utf-8")
    logger.info(
        "Wrote .book file to %s (%d page(s), %d chapter(s))",
        out_path,
        book["total_pages"],
        len(book["chapters"]),
    )
    return book
