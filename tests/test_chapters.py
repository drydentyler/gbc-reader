"""Tests for ``gbc_reader_prep.chapters``.

Fixture PDFs are built in-test using PyMuPDF's own ``set_toc`` so that no
external PDF files are needed for CI. This relies on ``set_toc`` and
``get_toc`` being inverses for the simple format ``[level, title, page]``
where ``page`` is 1-indexed.

Refs: A-3
"""

from __future__ import annotations

from pathlib import Path

import pytest

pymupdf = pytest.importorskip("pymupdf")

from gbc_reader_prep.chapters import (  # noqa: E402  (after importorskip)
    Chapter,
    detect_chapters,
    detect_chapters_from_heuristic,
    detect_chapters_from_heuristic_path,
    detect_chapters_from_outline,
    detect_chapters_from_outline_path,
    detect_chapters_path,
    top_level_chapters,
)


def _make_pdf_with_toc(
    path: Path, page_count: int, toc: list[list]
) -> None:
    """Create a small PDF at ``path`` with ``page_count`` blank pages and
    the given outline.

    ``toc`` follows PyMuPDF's simple format: each entry is
    ``[level, title, page_1_indexed]``.
    """
    doc = pymupdf.open()
    try:
        for _ in range(page_count):
            doc.new_page()
        if toc:
            doc.set_toc(toc)
        doc.save(str(path))
    finally:
        doc.close()


def _make_pdf_with_text_pages(path: Path, pages: list[str]) -> None:
    """Create a PDF at ``path`` with one page per string in ``pages``,
    each page's first line of text set to the given string.

    No outline is set, so this fixture exercises the heuristic fallback.
    """
    doc = pymupdf.open()
    try:
        for text in pages:
            page = doc.new_page()
            page.insert_text((72, 72), text)
        doc.save(str(path))
    finally:
        doc.close()


def test_detect_chapters_with_outline(tmp_path: Path) -> None:
    pdf = tmp_path / "with_toc.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=10,
        toc=[
            [1, "Chapter 1", 1],
            [1, "Chapter 2", 4],
            [2, "Section 2.1", 5],
            [1, "Chapter 3", 8],
        ],
    )

    chapters = detect_chapters_from_outline_path(pdf)

    assert chapters == [
        Chapter(title="Chapter 1", start_page=0, level=1),
        Chapter(title="Chapter 2", start_page=3, level=1),
        Chapter(title="Section 2.1", start_page=4, level=2),
        Chapter(title="Chapter 3", start_page=7, level=1),
    ]


def test_detect_chapters_drops_cover_entry_linked_to_back_of_book(
    tmp_path: Path,
) -> None:
    """A 'Cover' outline entry that resolves to a page other than the
    first page (e.g. a cover image scan placed at the back of the book)
    must be dropped rather than treated as where the book begins.

    Regression test for issue #37 / A-4.
    """
    pdf = tmp_path / "misplaced_cover.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=10,
        toc=[
            [1, "Cover", 9],
            [1, "Title Page", 1],
            [1, "Copyright", 2],
            [1, "Chapter 1", 3],
        ],
    )

    chapters = detect_chapters_from_outline_path(pdf)

    assert chapters == [
        Chapter(title="Title Page", start_page=0, level=1),
        Chapter(title="Copyright", start_page=1, level=1),
        Chapter(title="Chapter 1", start_page=2, level=1),
    ]


def test_detect_chapters_keeps_cover_entry_on_first_page(
    tmp_path: Path,
) -> None:
    """A 'Cover' entry that correctly resolves to the first page is kept."""
    pdf = tmp_path / "correct_cover.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=3,
        toc=[
            [1, "Cover", 1],
            [1, "Chapter 1", 2],
        ],
    )

    chapters = detect_chapters_from_outline_path(pdf)

    assert chapters == [
        Chapter(title="Cover", start_page=0, level=1),
        Chapter(title="Chapter 1", start_page=1, level=1),
    ]


def test_detect_chapters_cover_check_is_case_insensitive(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "cover_case.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=5,
        toc=[
            [1, "COVER", 5],
            [1, "Title Page", 1],
        ],
    )

    chapters = detect_chapters_from_outline_path(pdf)

    assert chapters == [Chapter(title="Title Page", start_page=0, level=1)]


def test_detect_chapters_no_outline(tmp_path: Path) -> None:
    pdf = tmp_path / "no_toc.pdf"
    _make_pdf_with_toc(pdf, page_count=3, toc=[])

    chapters = detect_chapters_from_outline_path(pdf)
    assert chapters == []


def test_detect_chapters_strips_title_whitespace(tmp_path: Path) -> None:
    pdf = tmp_path / "whitespace.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=2,
        toc=[[1, "  Spacy Title  ", 1]],
    )

    chapters = detect_chapters_from_outline_path(pdf)
    assert chapters == [Chapter(title="Spacy Title", start_page=0, level=1)]


def test_detect_chapters_pages_are_zero_indexed(tmp_path: Path) -> None:
    """get_toc returns 1-based pages; our Chapter records must be 0-based."""
    pdf = tmp_path / "indexing.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=5,
        toc=[
            [1, "First", 1],
            [1, "Middle", 3],
            [1, "Last", 5],
        ],
    )
    chapters = detect_chapters_from_outline_path(pdf)
    assert [c.start_page for c in chapters] == [0, 2, 4]


def test_detect_chapters_preserves_outline_order(tmp_path: Path) -> None:
    pdf = tmp_path / "order.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=6,
        toc=[
            [1, "Alpha", 1],
            [1, "Beta", 2],
            [1, "Gamma", 3],
        ],
    )
    titles = [c.title for c in detect_chapters_from_outline_path(pdf)]
    assert titles == ["Alpha", "Beta", "Gamma"]


def test_detect_chapters_records_hierarchy_level(tmp_path: Path) -> None:
    pdf = tmp_path / "levels.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=4,
        toc=[
            [1, "Top", 1],
            [2, "Mid", 2],
            [3, "Deep", 3],
        ],
    )
    chapters = detect_chapters_from_outline_path(pdf)
    assert [c.level for c in chapters] == [1, 2, 3]


def test_top_level_chapters_filters_to_level_one() -> None:
    chapters = [
        Chapter("Top A", 0, 1),
        Chapter("Sub A.1", 2, 2),
        Chapter("Top B", 5, 1),
        Chapter("Sub B.1", 7, 2),
        Chapter("Sub B.1.1", 8, 3),
        Chapter("Top C", 10, 1),
    ]
    assert top_level_chapters(chapters) == [
        Chapter("Top A", 0, 1),
        Chapter("Top B", 5, 1),
        Chapter("Top C", 10, 1),
    ]


def test_top_level_chapters_empty_input() -> None:
    assert top_level_chapters([]) == []


def test_detect_chapters_from_outline_path_missing_file(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does-not-exist.pdf"
    with pytest.raises(FileNotFoundError):
        detect_chapters_from_outline_path(missing)


def test_detect_chapters_from_outline_accepts_open_document(
    tmp_path: Path,
) -> None:
    """The library-level entry point accepts a Document directly."""
    pdf = tmp_path / "direct.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=2,
        toc=[[1, "Only Chapter", 1]],
    )
    doc = pymupdf.open(str(pdf))
    try:
        chapters = detect_chapters_from_outline(doc)
    finally:
        doc.close()
    assert chapters == [Chapter(title="Only Chapter", start_page=0, level=1)]


def test_detect_chapters_from_heuristic_matches_chapter_lines(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "heuristic_chapters.pdf"
    _make_pdf_with_text_pages(
        pdf,
        pages=[
            "Some front matter text.",
            "Chapter 1\nIt was a dark and stormy night.",
            "More body text.",
            "Chapter 2\nThe next morning.",
        ],
    )
    chapters = detect_chapters_from_heuristic_path(pdf)
    assert chapters == [
        Chapter(title="Chapter 1", start_page=1, level=1),
        Chapter(title="Chapter 2", start_page=3, level=1),
    ]


def test_detect_chapters_from_heuristic_matches_named_sections(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "heuristic_named.pdf"
    _make_pdf_with_text_pages(
        pdf,
        pages=[
            "Prologue\nBefore it all began.",
            "Chapter 1\nThe story starts.",
            "Epilogue\nAfter it all ended.",
        ],
    )
    chapters = detect_chapters_from_heuristic_path(pdf)
    assert [c.title for c in chapters] == ["Prologue", "Chapter 1", "Epilogue"]


def test_detect_chapters_from_heuristic_is_case_insensitive(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "heuristic_case.pdf"
    _make_pdf_with_text_pages(pdf, pages=["CHAPTER 1\nBody text."])
    chapters = detect_chapters_from_heuristic_path(pdf)
    assert chapters == [Chapter(title="CHAPTER 1", start_page=0, level=1)]


def test_detect_chapters_from_heuristic_no_matches(tmp_path: Path) -> None:
    pdf = tmp_path / "heuristic_none.pdf"
    _make_pdf_with_text_pages(pdf, pages=["Just some text.", "More text."])
    assert detect_chapters_from_heuristic_path(pdf) == []


def test_detect_chapters_from_heuristic_path_missing_file(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does-not-exist.pdf"
    with pytest.raises(FileNotFoundError):
        detect_chapters_from_heuristic_path(missing)


def test_detect_chapters_from_heuristic_accepts_open_document(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "heuristic_direct.pdf"
    _make_pdf_with_text_pages(pdf, pages=["Introduction\nWelcome."])
    doc = pymupdf.open(str(pdf))
    try:
        chapters = detect_chapters_from_heuristic(doc)
    finally:
        doc.close()
    assert chapters == [Chapter(title="Introduction", start_page=0, level=1)]


def test_detect_chapters_prefers_outline_when_present(tmp_path: Path) -> None:
    """detect_chapters should not fall back to heuristic matching when
    the PDF already has a usable outline."""
    pdf = tmp_path / "combined_with_outline.pdf"
    _make_pdf_with_toc(
        pdf,
        page_count=3,
        toc=[[1, "Chapter 1", 1], [1, "Chapter 2", 2]],
    )
    chapters = detect_chapters_path(pdf)
    assert chapters == [
        Chapter(title="Chapter 1", start_page=0, level=1),
        Chapter(title="Chapter 2", start_page=1, level=1),
    ]


def test_detect_chapters_falls_back_to_heuristic_without_outline(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "combined_without_outline.pdf"
    _make_pdf_with_text_pages(
        pdf,
        pages=["Chapter 1\nText.", "Chapter 2\nMore text."],
    )
    chapters = detect_chapters_path(pdf)
    assert chapters == [
        Chapter(title="Chapter 1", start_page=0, level=1),
        Chapter(title="Chapter 2", start_page=1, level=1),
    ]


def test_detect_chapters_accepts_open_document(tmp_path: Path) -> None:
    pdf = tmp_path / "combined_direct.pdf"
    _make_pdf_with_text_pages(pdf, pages=["Chapter 1\nText."])
    doc = pymupdf.open(str(pdf))
    try:
        chapters = detect_chapters(doc)
    finally:
        doc.close()
    assert chapters == [Chapter(title="Chapter 1", start_page=0, level=1)]
