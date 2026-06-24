"""Front/back matter trimming.

Ticket: A-5 — Front/back matter trimming.

Given a chapter list (from :mod:`gbc_reader_prep.chapters`) and a PDF's
total page count, decide which pages constitute the book's "main
content" by trimming off back matter such as appendices, notes,
bibliographies, and indexes.

This module is framework-agnostic: no argparse, no CLI concerns. The
``preprocess`` subcommand (see ``preprocess.py``) is responsible for
turning a :class:`TrimResult` into a dry-run report and for applying
any user-supplied ``--start-page``/``--end-page`` overrides.

Front matter is not currently trimmed: the first detected chapter
(if any) is just informational. Per the project plan §3.1, front-matter
trimming is folded into "main content start" detection, but since A-3/A-4
already report the first chapter as the start of the book's content, this
ticket focuses on the back-matter half of the problem, which the A-4
synopsis specifically flagged as the open issue (false-positive ToC
matches and undetected appendices/indexes).

Refs: A-5
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .chapters import Chapter

logger = logging.getLogger(__name__)

# Titles matched against each detected chapter's title (case-insensitive,
# anchored to the start of the title) to decide whether that chapter marks
# the start of back matter. Order does not matter — the *earliest* matching
# chapter in the book wins (see detect_content_bounds).
_BACK_MATTER_PATTERNS = [
    re.compile(r"^appendix\b", re.IGNORECASE),
    re.compile(r"^notes\b", re.IGNORECASE),
    re.compile(r"^bibliography\b", re.IGNORECASE),
    re.compile(r"^index\b", re.IGNORECASE),
    re.compile(r"^about the author\b", re.IGNORECASE),
    re.compile(r"^acknowledg(e?ments)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class TrimResult:
    """Proposed main-content page range for a book.

    Attributes:
        start_page: 0-indexed page where main content begins. Currently
            always the first detected chapter's start page, or 0 if no
            chapters were detected at all.
        end_page: 0-indexed page where main content ends, inclusive.
            ``page_count - 1`` unless a back-matter chapter was detected,
            in which case it is the page immediately before that chapter
            begins.
        back_matter_title: The title of the first detected back-matter
            chapter, or ``None`` if no back matter was detected.
        back_matter_start_page: The detected back-matter chapter's
            0-indexed start page, or ``None`` if no back matter was
            detected.
    """

    start_page: int
    end_page: int
    back_matter_title: str | None
    back_matter_start_page: int | None


def detect_back_matter_chapter(chapters: list[Chapter]) -> Chapter | None:
    """Return the earliest chapter (by ``start_page``) whose title matches
    a known back-matter pattern (Appendix, Notes, Bibliography, Index,
    About the Author, Acknowledgments).

    Args:
        chapters: Chapter list, typically from
            :func:`gbc_reader_prep.chapters.detect_chapters`.

    Returns:
        The matching :class:`Chapter` with the smallest ``start_page``,
        or ``None`` if no chapter matches.
    """
    matches = [
        chapter
        for chapter in chapters
        if any(pattern.match(chapter.title) for pattern in _BACK_MATTER_PATTERNS)
    ]
    if not matches:
        return None
    return min(matches, key=lambda chapter: chapter.start_page)


def detect_content_bounds(chapters: list[Chapter], page_count: int) -> TrimResult:
    """Propose a main-content page range, trimming detected back matter.

    Args:
        chapters: Chapter list, typically from
            :func:`gbc_reader_prep.chapters.detect_chapters`.
        page_count: Total number of pages in the PDF.

    Returns:
        A :class:`TrimResult` describing the proposed start/end pages.

    Raises:
        ValueError: If ``page_count`` is not positive.
    """
    if page_count < 1:
        raise ValueError(f"page_count must be positive, got {page_count}")

    start_page = chapters[0].start_page if chapters else 0
    end_page = page_count - 1

    back_matter = detect_back_matter_chapter(chapters)
    back_matter_title = None
    back_matter_start_page = None
    if back_matter is not None and back_matter.start_page > start_page:
        back_matter_title = back_matter.title
        back_matter_start_page = back_matter.start_page
        end_page = back_matter.start_page - 1
        logger.info(
            "Detected back matter %r at page %d; proposing end page %d",
            back_matter_title,
            back_matter_start_page,
            end_page,
        )
    else:
        logger.info("No back matter detected; proposing end page %d", end_page)

    return TrimResult(
        start_page=start_page,
        end_page=end_page,
        back_matter_title=back_matter_title,
        back_matter_start_page=back_matter_start_page,
    )
