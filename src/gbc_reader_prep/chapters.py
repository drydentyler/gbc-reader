"""Chapter detection from a PDF's outline (bookmark tree).

This module is framework-agnostic: it takes a PyMuPDF Document (or a path
to a PDF) and returns a list of Chapter records. It knows nothing about
argparse, the CLI, or any other higher-level concern.

If the PDF has no outline, ``detect_chapters_from_outline`` returns an
empty list and logs a warning. The heuristic fallback for outline-less
PDFs is the responsibility of ticket A-4 (see
``GBC_Reader_Project_Plan.md`` §4 Epic A).

Page indexing convention
------------------------
PyMuPDF's ``Document.get_toc()`` returns 1-based page numbers (see
https://pymupdf.readthedocs.io/en/latest/document.html). Entries that do
not resolve to a page (external links, named destinations that could not
be resolved) are reported with page == -1.

Inside this project we store and pass page numbers as **0-based**
integers throughout, matching iteration over ``Document`` pages and the
project's existing internal conventions. ``detect_chapters_from_outline``
performs the conversion exactly once, at the boundary between PyMuPDF
output and our domain model. Downstream code should never see a 1-based
page number from this module.

Refs: A-3
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pymupdf  # noqa: F401  (only used for type hints)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chapter:
    """A single chapter (or sub-chapter) detected from a PDF's outline.

    Attributes:
        title: The chapter's title as it appears in the outline, with
            leading/trailing whitespace stripped. Internal whitespace is
            preserved unchanged.
        start_page: Zero-indexed page number where the chapter begins.
            Converted from PyMuPDF's 1-indexed ``get_toc()`` output.
        level: Outline nesting depth as reported by PyMuPDF. 1 is the
            top level; the first outline entry is always level 1.
    """

    title: str
    start_page: int
    level: int


def detect_chapters_from_outline(doc: "pymupdf.Document") -> list[Chapter]:
    """Extract a chapter list from a PDF's outline (bookmark tree).

    Calls ``doc.get_toc(simple=True)`` and converts each entry into a
    :class:`Chapter`. Page numbers are converted from PyMuPDF's 1-based
    convention to this project's 0-based convention.

    Entries whose page number is not positive (PyMuPDF emits -1 for
    outline entries that do not resolve to a concrete page, e.g. external
    links or unresolved named destinations) are skipped, with a single
    summary warning logged at the end if any were dropped.

    Args:
        doc: An open PyMuPDF Document.

    Returns:
        A list of :class:`Chapter` objects in outline order. Empty list
        if the PDF has no outline at all.
    """
    toc = doc.get_toc(simple=True)
    if not toc:
        logger.warning(
            "PDF has no outline; outline-based chapter detection yields no chapters"
        )
        return []

    chapters: list[Chapter] = []
    skipped = 0
    for entry in toc:
        # Defensive: PyMuPDF's documented format is [lvl, title, page] in
        # simple mode, but we use indexed access (not unpacking) to tolerate
        # any future extra fields without raising.
        level = entry[0]
        title = entry[1]
        page_1_indexed = entry[2]

        if page_1_indexed < 1:
            skipped += 1
            logger.debug(
                "Skipping outline entry %r at level %d: unresolved page (%d)",
                title,
                level,
                page_1_indexed,
            )
            continue

        chapters.append(
            Chapter(
                title=title.strip(),
                start_page=page_1_indexed - 1,
                level=level,
            )
        )

    if skipped:
        logger.warning(
            "Skipped %d outline entries with no resolvable page", skipped
        )
    logger.info("Detected %d chapter entries from outline", len(chapters))
    return chapters


def detect_chapters_from_outline_path(pdf_path: Path | str) -> list[Chapter]:
    """Convenience wrapper that opens ``pdf_path``, runs
    :func:`detect_chapters_from_outline`, and closes the document.

    Args:
        pdf_path: Path to the input PDF.

    Returns:
        List of :class:`Chapter` objects from the PDF's outline (empty
        list if the PDF has no outline).

    Raises:
        FileNotFoundError: If ``pdf_path`` does not exist.
    """
    # Imported here so this module remains importable for tooling that
    # only needs the Chapter dataclass without paying the pymupdf import
    # cost. (pymupdf imports the MuPDF binary on first import.)
    import pymupdf

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = pymupdf.open(str(pdf_path))
    try:
        return detect_chapters_from_outline(doc)
    finally:
        doc.close()


def top_level_chapters(chapters: list[Chapter]) -> list[Chapter]:
    """Return only level-1 entries from a chapter list.

    Useful for callers that want top-of-book chapters and not their
    sub-sections. Preserves the input order.

    Args:
        chapters: A list of :class:`Chapter` objects (typically the
            return value of :func:`detect_chapters_from_outline`).

    Returns:
        A new list containing only the entries whose ``level`` is 1.
    """
    return [c for c in chapters if c.level == 1]
