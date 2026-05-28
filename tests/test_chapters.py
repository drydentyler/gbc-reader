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
    detect_chapters_from_outline,
    detect_chapters_from_outline_path,
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
