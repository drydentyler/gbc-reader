"""Tests for the ``.book`` file writer.

Ticket: A-8.
"""

from __future__ import annotations

import base64
import json

import pytest

from gbc_reader_prep.book import build_book, write_book_path
from gbc_reader_prep.cli import main


def _make_pdf(tmp_path, *, with_toc: bool = True, title: str | None = None):
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "book.pdf"
    doc = pymupdf.open()

    page = doc.new_page()
    page.insert_text((50, 50), "Cover Title", fontsize=24)

    page = doc.new_page()
    page.insert_text((50, 50), "Chapter 1")
    page.insert_text((50, 80), "This is the first chapter's body text. " * 5)

    page = doc.new_page()
    page.insert_text((50, 50), "Chapter 2")
    page.insert_text((50, 80), "This is the second chapter's body text. " * 5)

    if with_toc:
        doc.set_toc([[1, "Chapter 1", 2], [1, "Chapter 2", 3]])
    if title is not None:
        doc.set_metadata({"title": title, "author": "Test Author"})

    doc.save(str(pdf))
    doc.close()
    return pdf


def test_build_book_has_expected_schema_fields(tmp_path):
    pdf = _make_pdf(tmp_path, title="My Book")
    book = build_book(pdf)

    assert book["schema_version"] == 1
    assert book["title"] == "My Book"
    assert book["author"] == "Test Author"
    assert book["display"] == {
        "width_px": 400,
        "height_px": 240,
        "font": "6x10",
    }
    assert book["total_pages"] == len(book["pages"])
    assert book["total_pages"] > 0


def test_build_book_title_falls_back_to_filename_stem(tmp_path):
    pdf = _make_pdf(tmp_path, title=None)
    book = build_book(pdf)
    assert book["title"] == pdf.stem
    assert book["author"] == ""


def test_build_book_chapters_match_detected_chapters(tmp_path):
    pdf = _make_pdf(tmp_path)
    book = build_book(pdf)

    assert len(book["chapters"]) == 2
    assert book["chapters"][0] == {"id": 0, "title": "Chapter 1", "start_page": 1}
    assert book["chapters"][1] == {"id": 1, "title": "Chapter 2", "start_page": 2}


def test_build_book_pages_reference_valid_chapter_ids(tmp_path):
    pdf = _make_pdf(tmp_path)
    book = build_book(pdf)

    chapter_ids = {c["id"] for c in book["chapters"]}
    for page in book["pages"]:
        assert page["chapter_id"] in chapter_ids
        assert isinstance(page["lines"], list)


def test_build_book_cover_is_valid_base64_png(tmp_path):
    pdf = _make_pdf(tmp_path)
    book = build_book(pdf)

    assert book["cover_png_base64"] is not None
    decoded = base64.b64decode(book["cover_png_base64"])
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_book_without_cover_sets_field_none(tmp_path):
    pdf = _make_pdf(tmp_path)
    book = build_book(pdf, include_cover=False)
    assert book["cover_png_base64"] is None


def test_build_book_respects_start_end_page_overrides(tmp_path):
    pdf = _make_pdf(tmp_path)
    book_full = build_book(pdf, include_cover=False)
    book_ch1_only = build_book(pdf, start_page=1, end_page=1, include_cover=False)

    assert len(book_ch1_only["chapters"]) == 1
    assert book_ch1_only["chapters"][0]["title"] == "Chapter 1"
    assert book_ch1_only["total_pages"] < book_full["total_pages"]


def test_build_book_missing_pdf_raises(tmp_path):
    missing = tmp_path / "does-not-exist.pdf"
    with pytest.raises(FileNotFoundError):
        build_book(missing)


def test_write_book_path_writes_valid_json_file(tmp_path):
    pdf = _make_pdf(tmp_path, title="My Book")
    out = tmp_path / "out" / "mybook.book"

    book = write_book_path(pdf, out, include_cover=False)

    assert out.exists()
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk == book
    assert on_disk["title"] == "My Book"


def test_cli_preprocess_book_output_writes_book_file(tmp_path):
    pdf = _make_pdf(tmp_path, title="My Book")
    out = tmp_path / "out" / "mybook.book"

    assert main(["preprocess", str(pdf), "-o", str(out)]) == 0
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["title"] == "My Book"
    assert data["total_pages"] > 0
    assert len(data["chapters"]) == 2
    assert data["cover_png_base64"] is not None


def test_cli_preprocess_book_output_missing_pdf_returns_two(tmp_path):
    missing = tmp_path / "does-not-exist.pdf"
    out = tmp_path / "out" / "mybook.book"
    assert main(["preprocess", str(missing), "-o", str(out)]) == 2


def test_cli_preprocess_book_output_respects_page_overrides(tmp_path):
    pdf = _make_pdf(tmp_path)
    out = tmp_path / "out" / "mybook.book"

    assert (
        main(
            [
                "preprocess",
                str(pdf),
                "-o",
                str(out),
                "--start-page",
                "1",
                "--end-page",
                "1",
            ]
        )
        == 0
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["chapters"]) == 1
    assert data["chapters"][0]["title"] == "Chapter 1"


def test_cli_preprocess_book_output_missing_font_metrics_returns_two(tmp_path):
    pdf = _make_pdf(tmp_path)
    out = tmp_path / "out" / "mybook.book"
    missing_metrics = tmp_path / "does-not-exist.json"

    assert (
        main(
            [
                "preprocess",
                str(pdf),
                "-o",
                str(out),
                "--font-metrics",
                str(missing_metrics),
            ]
        )
        == 2
    )
    assert not out.exists()
