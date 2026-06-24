"""Pagination engine: lay out extracted text into fixed-size display pages.

Ticket: A-7 — Pagination engine.

Given per-PDF-page extracted text (see :mod:`gbc_reader_prep.extract`) and a
chapter list (see :mod:`gbc_reader_prep.chapters`), reflow the text into
``Page`` records sized to the target display (400x240 by default) using a
fixed-width font metrics model. This module is framework-agnostic: no
argparse, no CLI concerns.

Hard rule (per the project plan, §3.1): a chapter's first page always
begins with that chapter's first line at the top of the display. This is
enforced by flushing (and blank-padding) any partially-filled page buffer
before starting a new chapter's text, rather than letting one chapter's
tail share a page with the next chapter's head.

Font metrics
------------
The firmware (B-4) has not yet picked a final bitmap font (see project
plan Q7), so this module works against a simple fixed-width character grid
model (``FontMetrics``: pixel width per character, pixel height per line)
rather than real glyph data. ``DEFAULT_FONT_METRICS`` is a placeholder
6x10px grid chosen to land in the ballpark of the acceptance criterion's
~250 words/page sanity check; it must be replaced with values matching the
real firmware font once B-4 lands, via ``--font-metrics`` or
``load_font_metrics``.

Refs: A-7
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .chapters import Chapter

logger = logging.getLogger(__name__)

DISPLAY_WIDTH = 400
DISPLAY_HEIGHT = 240


@dataclass(frozen=True)
class FontMetrics:
    """Fixed-width character grid used to compute how much text fits on a
    page.

    Attributes:
        char_width_px: Width of one monospace character cell, in pixels.
        line_height_px: Height of one line (including any inter-line
            spacing), in pixels.
    """

    char_width_px: int
    line_height_px: int


# Placeholder grid (6x10px) until B-4 picks the real firmware font and this
# gets replaced (or overridden via --font-metrics) with matching values.
DEFAULT_FONT_METRICS = FontMetrics(char_width_px=6, line_height_px=10)


@dataclass(frozen=True)
class Page:
    """A single laid-out page of text.

    Attributes:
        chapter_id: Index into the chapter list this page's text belongs
            to (0-based, in chapter order — matches the ``id`` field of
            the ``.book`` schema's ``chapters`` array per the project
            plan).
        lines: Page lines, top to bottom. Always exactly
            ``lines_per_page(...)`` entries; short pages are padded with
            empty strings so every page is a uniform fixed-size grid for
            the firmware to render.
        is_title_page: ``True`` if this page is a chapter title page (see
            :func:`make_title_page`) rather than body text.
    """

    chapter_id: int
    lines: list[str]
    is_title_page: bool = False


def center_line(text: str, width: int) -> str:
    """Center ``text`` within a line of ``width`` characters using spaces.

    If ``text`` is at least as long as ``width``, it is truncated to
    ``width`` rather than overflowing.

    Args:
        text: Text to center.
        width: Target line width, in characters.

    Returns:
        ``text`` padded with spaces on both sides (left gets the smaller
        half when the padding is odd), or truncated to ``width``.
    """
    if len(text) >= width:
        return text[:width]
    total_pad = width - len(text)
    left = total_pad // 2
    right = total_pad - left
    return " " * left + text + " " * right


def make_title_page(
    chapter_id: int,
    title: str,
    font_metrics: FontMetrics = DEFAULT_FONT_METRICS,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
) -> Page:
    """Build a blank chapter title page with ``title`` centered both
    horizontally and vertically.

    If ``title`` is longer than one line's width, it is word-wrapped into
    multiple lines first; that whole block of lines is then centered
    vertically as a unit. All other lines on the page are blank.

    Args:
        chapter_id: Chapter index this title page belongs to (see
            :attr:`Page.chapter_id`).
        title: Chapter title text to display.
        font_metrics: Character grid to lay out against. Defaults to
            :data:`DEFAULT_FONT_METRICS`.
        display_width: Display width in pixels. Defaults to 400.
        display_height: Display height in pixels. Defaults to 240.

    Returns:
        A :class:`Page` with ``is_title_page=True`` and exactly
        ``lines_per_page(...)`` lines.
    """
    max_chars = chars_per_line(font_metrics, display_width)
    max_lines = lines_per_page(font_metrics, display_height)

    title_lines = wrap_text(title, max_chars) or [""]
    title_lines = title_lines[:max_lines]

    blank_above = (max_lines - len(title_lines)) // 2
    blank_below = max_lines - len(title_lines) - blank_above

    lines = (
        [""] * blank_above
        + [center_line(line, max_chars) for line in title_lines]
        + [""] * blank_below
    )
    return Page(chapter_id=chapter_id, lines=lines, is_title_page=True)


def load_font_metrics(path: Path | str) -> FontMetrics:
    """Load font metrics from a JSON file.

    Expected shape: ``{"char_width_px": <int>, "line_height_px": <int>}``.

    Args:
        path: Path to the font metrics JSON file.

    Returns:
        The parsed :class:`FontMetrics`.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Font metrics file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return FontMetrics(
        char_width_px=int(data["char_width_px"]),
        line_height_px=int(data["line_height_px"]),
    )


def chars_per_line(font_metrics: FontMetrics, display_width: int = DISPLAY_WIDTH) -> int:
    """Maximum characters that fit on one line at the given display width."""
    return max(1, display_width // font_metrics.char_width_px)


def lines_per_page(font_metrics: FontMetrics, display_height: int = DISPLAY_HEIGHT) -> int:
    """Maximum lines that fit on one page at the given display height."""
    return max(1, display_height // font_metrics.line_height_px)


def wrap_text(text: str, max_chars: int) -> list[str]:
    """Greedily word-wrap ``text`` into lines no longer than ``max_chars``.

    Whitespace (including newlines from the extracted PDF text) is
    collapsed: words are joined back together with single spaces. A word
    longer than ``max_chars`` on its own is hard-split across lines rather
    than overflowing.

    Args:
        text: Source text (arbitrary whitespace).
        max_chars: Maximum line length, in characters.

    Returns:
        A list of lines, each at most ``max_chars`` characters. Empty list
        for blank input.
    """
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        if len(word) > max_chars:
            if current:
                lines.append(current)
                current = ""
            for i in range(0, len(word), max_chars):
                chunk = word[i : i + max_chars]
                if i + max_chars >= len(word):
                    current = chunk
                else:
                    lines.append(chunk)
            continue

        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


_HEADING_PREFIX_PATTERNS = [
    re.compile(r"^chapter\s+\d+\b", re.IGNORECASE),
    re.compile(r"^part\s+(?:[ivxlcdm]+|\d+)\b", re.IGNORECASE),
    re.compile(r"^section\s+\d+\b", re.IGNORECASE),
    re.compile(r"^prologue\b", re.IGNORECASE),
    re.compile(r"^epilogue\b", re.IGNORECASE),
    re.compile(r"^introduction\b", re.IGNORECASE),
]


def _strip_heading_prefixes(text: str) -> str:
    """Repeatedly strip any leading ``_HEADING_PREFIX_PATTERNS`` match (and
    the punctuation/whitespace immediately following it) from ``text``."""
    changed = True
    while changed:
        changed = False
        for pattern in _HEADING_PREFIX_PATTERNS:
            match = pattern.match(text)
            if match:
                text = text[match.end() :].lstrip(" :.-")
                changed = True
    return text


def strip_chapter_heading(text: str, title: str) -> str:
    """Strip a leading chapter-heading restatement from ``text``.

    The extracted page text for a chapter's first page typically still
    contains that chapter's own heading (e.g. ``"Chapter 1 Some Title"``
    or ``"Part I: Nonhuman Minds"``) — now redundant since
    :func:`make_title_page` already displays it on its own dedicated title
    page. This repeatedly strips, from the start of ``text``, any
    combination of: a known heading-prefix pattern (``Chapter N``, ``Part
    N``/roman numeral, ``Section N``, ``Prologue``, ``Epilogue``,
    ``Introduction``); a literal restatement of ``title``; or, if
    ``title`` itself begins with one of those same prefix patterns (e.g.
    a title of ``"Part I: Nonhuman Minds"`` or ``"Introduction: Hard
    Calls and Easy Calls"``), a restatement of just the bare subtitle
    after that label (``"Nonhuman Minds"`` / ``"Hard Calls and Easy
    Calls"``) — since the source PDF may render the numbered/labeled
    prefix and the subtitle as separate heading lines rather than
    ``title`` verbatim. Stripping continues, in any order, until none of
    these match any more.

    Args:
        text: Whitespace-arbitrary chapter body text (e.g. from joining
            several PDF pages' extracted text).
        title: The chapter's title, as detected (see :class:`Chapter`).

    Returns:
        ``text`` with whitespace collapsed to single spaces and any
        leading heading restatement removed. Unchanged (aside from
        whitespace collapsing) if no heading match is found at the start.
    """
    collapsed = " ".join(text.split())
    title_norm = " ".join(title.split())
    bare_title = _strip_heading_prefixes(title_norm) if title_norm else ""

    candidates = [c for c in (title_norm, bare_title) if c]

    changed = True
    while changed:
        changed = False
        for pattern in _HEADING_PREFIX_PATTERNS:
            match = pattern.match(collapsed)
            if match:
                collapsed = collapsed[match.end() :].lstrip(" :.-")
                changed = True
        for candidate in candidates:
            if collapsed.lower().startswith(candidate.lower()):
                collapsed = collapsed[len(candidate) :].lstrip(" :.-")
                changed = True

    return collapsed


def paginate_chapters(
    page_texts: list[str],
    chapters: list[Chapter],
    font_metrics: FontMetrics = DEFAULT_FONT_METRICS,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
    start_page: int = 0,
    end_page: int | None = None,
) -> list[Page]:
    """Lay out extracted PDF text into fixed-size display pages.

    Text is grouped by chapter (each chapter's text runs from its
    ``start_page`` up to but not including the next chapter's
    ``start_page``, clamped to ``[start_page, end_page]``), word-wrapped to
    the display's character grid, and chunked into pages of
    ``lines_per_page(font_metrics, display_height)`` lines.

    The chapter-start-at-top rule is enforced by flushing (and
    blank-padding) any partially-filled page buffer before a new chapter's
    text begins, so a chapter never starts partway down a page that also
    holds the previous chapter's tail. Immediately after that flush, if
    the chapter has a non-blank title, a title page (see
    :func:`make_title_page`) is inserted before the chapter's body text —
    so each named chapter's body always starts on the page *after* its
    title page. The synthetic single-chapter fallback used when no
    chapters are detected has a blank title and so gets no title page.
    For the same reason, a chapter's text has any leading restatement of
    its own heading (e.g. "Chapter 1 Some Title", already shown on the
    title page) stripped via :func:`strip_chapter_heading` before
    word-wrapping, so it isn't shown twice.

    Args:
        page_texts: Extracted text for every PDF page, 0-indexed (e.g. from
            :func:`gbc_reader_prep.extract.extract_text_pages`).
        chapters: Chapter list (e.g. from
            :func:`gbc_reader_prep.chapters.detect_chapters`). Chapters
            outside ``[start_page, end_page]`` are ignored. If none fall
            in range, the whole range is treated as a single unnamed
            chapter.
        font_metrics: Character grid to lay out against. Defaults to
            :data:`DEFAULT_FONT_METRICS`.
        display_width: Display width in pixels. Defaults to 400.
        display_height: Display height in pixels. Defaults to 240.
        start_page: First PDF page (0-indexed, inclusive) to include.
            Defaults to 0.
        end_page: Last PDF page (0-indexed, inclusive) to include.
            Defaults to ``len(page_texts) - 1``.

    Returns:
        A list of :class:`Page` records in reading order. Empty if the
        page range contains no non-whitespace text.
    """
    if end_page is None:
        end_page = len(page_texts) - 1

    relevant = sorted(
        (c for c in chapters if start_page <= c.start_page <= end_page),
        key=lambda c: c.start_page,
    )
    if not relevant:
        relevant = [Chapter(title="", start_page=start_page, level=1)]

    max_chars = chars_per_line(font_metrics, display_width)
    max_lines = lines_per_page(font_metrics, display_height)

    pages: list[Page] = []
    current_lines: list[str] = []
    current_chapter_id = 0

    def flush_page() -> None:
        nonlocal current_lines
        if not current_lines:
            return
        padded = current_lines + [""] * (max_lines - len(current_lines))
        pages.append(Page(chapter_id=current_chapter_id, lines=padded))
        current_lines = []

    for chapter_id, chapter in enumerate(relevant):
        chap_start = max(chapter.start_page, start_page)
        next_start = (
            relevant[chapter_id + 1].start_page
            if chapter_id + 1 < len(relevant)
            else end_page + 1
        )
        chap_end = min(next_start - 1, end_page)
        if chap_end < chap_start:
            continue

        text = " ".join(page_texts[p] for p in range(chap_start, chap_end + 1))
        if chapter.title.strip():
            text = strip_chapter_heading(text, chapter.title)
        lines = wrap_text(text, max_chars)
        if not lines:
            continue

        # Chapter-start-at-top: never let a new chapter share a page with
        # the previous chapter's leftover lines.
        flush_page()
        current_chapter_id = chapter_id

        if chapter.title.strip():
            pages.append(
                make_title_page(
                    chapter_id,
                    chapter.title,
                    font_metrics=font_metrics,
                    display_width=display_width,
                    display_height=display_height,
                )
            )

        for line in lines:
            current_lines.append(line)
            if len(current_lines) == max_lines:
                flush_page()
                current_chapter_id = chapter_id

    flush_page()

    logger.info(
        "Paginated pages %d-%d into %d display page(s) across %d chapter(s)",
        start_page,
        end_page,
        len(pages),
        len(relevant),
    )
    return pages


def paginate_path(
    pdf_path: Path | str,
    font_metrics: FontMetrics = DEFAULT_FONT_METRICS,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
    start_page: int | None = None,
    end_page: int | None = None,
) -> list[Page]:
    """Path-based convenience wrapper around :func:`paginate_chapters`.

    Opens ``pdf_path``, detects chapters (outline, falling back to
    heuristic text matching), extracts per-page text, and — if
    ``start_page``/``end_page`` are not given — proposes main-content
    bounds via :func:`gbc_reader_prep.trim.detect_content_bounds`.

    Args:
        pdf_path: Path to the input PDF.
        font_metrics: Character grid to lay out against. Defaults to
            :data:`DEFAULT_FONT_METRICS`.
        display_width: Display width in pixels. Defaults to 400.
        display_height: Display height in pixels. Defaults to 240.
        start_page: Override for the main-content start page (0-indexed).
            Auto-detected via :mod:`gbc_reader_prep.trim` if omitted.
        end_page: Override for the main-content end page (0-indexed,
            inclusive). Auto-detected via :mod:`gbc_reader_prep.trim` if
            omitted.

    Returns:
        See :func:`paginate_chapters`.

    Raises:
        FileNotFoundError: If ``pdf_path`` does not exist.
    """
    from .chapters import detect_chapters_path
    from .extract import extract_text_pages
    from .trim import detect_content_bounds

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    chapters = detect_chapters_path(pdf_path)
    page_texts = extract_text_pages(pdf_path)

    if start_page is None or end_page is None:
        bounds = detect_content_bounds(chapters, len(page_texts))
        if start_page is None:
            start_page = bounds.start_page
        if end_page is None:
            end_page = bounds.end_page

    return paginate_chapters(
        page_texts,
        chapters,
        font_metrics=font_metrics,
        display_width=display_width,
        display_height=display_height,
        start_page=start_page,
        end_page=end_page,
    )
