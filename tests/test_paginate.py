"""Tests for ``gbc_reader_prep.paginate``.

Refs: A-7
"""

from __future__ import annotations

import json

import pytest

from gbc_reader_prep.chapters import Chapter
from gbc_reader_prep.cli import main
from gbc_reader_prep.paginate import (
    DEFAULT_FONT_METRICS,
    FontMetrics,
    chars_per_line,
    lines_per_page,
    load_font_metrics,
    paginate_chapters,
    paginate_path,
    wrap_text,
)


def test_chars_per_line_and_lines_per_page():
    metrics = FontMetrics(char_width_px=10, line_height_px=20)
    assert chars_per_line(metrics, display_width=400) == 40
    assert lines_per_page(metrics, display_height=240) == 12


def test_chars_per_line_clamps_to_at_least_one():
    metrics = FontMetrics(char_width_px=1000, line_height_px=1000)
    assert chars_per_line(metrics, display_width=400) == 1
    assert lines_per_page(metrics, display_height=240) == 1


def test_wrap_text_basic_word_wrap():
    lines = wrap_text("the quick brown fox jumps over", max_chars=10)
    assert all(len(line) <= 10 for line in lines)
    assert " ".join(lines).split() == "the quick brown fox jumps over".split()


def test_wrap_text_hard_splits_long_word():
    lines = wrap_text("a" * 25, max_chars=10)
    assert lines == ["a" * 10, "a" * 10, "a" * 5]


def test_wrap_text_empty_input():
    assert wrap_text("", max_chars=10) == []
    assert wrap_text("   ", max_chars=10) == []


def test_wrap_text_collapses_whitespace():
    lines = wrap_text("line one\nline   two\n\nline three", max_chars=80)
    assert lines == ["line one line two line three"]


def test_load_font_metrics_reads_json(tmp_path):
    path = tmp_path / "font.json"
    path.write_text(json.dumps({"char_width_px": 8, "line_height_px": 16}))
    metrics = load_font_metrics(path)
    assert metrics == FontMetrics(char_width_px=8, line_height_px=16)


def test_load_font_metrics_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_font_metrics(tmp_path / "does-not-exist.json")


def test_paginate_chapters_no_chapters_treated_as_single_chapter():
    metrics = FontMetrics(char_width_px=10, line_height_px=20)  # 40 chars/line, 12 lines/page
    page_texts = ["word " * 200]
    pages = paginate_chapters(page_texts, [], font_metrics=metrics)
    assert len(pages) >= 1
    assert all(p.chapter_id == 0 for p in pages)
    assert all(len(p.lines) == 12 for p in pages)


def test_paginate_chapters_short_text_pads_with_blank_lines():
    metrics = FontMetrics(char_width_px=10, line_height_px=20)
    page_texts = ["hello world"]
    pages = paginate_chapters(page_texts, [], font_metrics=metrics)
    assert len(pages) == 1
    assert pages[0].lines[0] == "hello world"
    assert pages[0].lines[1:] == [""] * 11


def test_paginate_chapters_enforces_chapter_start_at_top():
    metrics = FontMetrics(char_width_px=10, line_height_px=20)  # 40 chars/line, 12 lines/page
    chapters = [
        Chapter(title="Chapter 1", start_page=0, level=1),
        Chapter(title="Chapter 2", start_page=1, level=1),
    ]
    # Chapter 1's text is short — well under one page.
    page_texts = ["short chapter one text", "chapter two begins here " * 100]

    pages = paginate_chapters(page_texts, chapters, font_metrics=metrics)

    chapter_1_pages = [p for p in pages if p.chapter_id == 0]
    chapter_2_pages = [p for p in pages if p.chapter_id == 1]
    assert len(chapter_1_pages) == 1
    assert len(chapter_2_pages) >= 1
    # Chapter 2's first page must start with chapter 2's first word, not
    # share a page with chapter 1's leftover lines.
    assert chapter_2_pages[0].lines[0].startswith("chapter two begins here")


def test_paginate_chapters_respects_start_end_page_bounds():
    metrics = FontMetrics(char_width_px=10, line_height_px=20)
    chapters = [
        Chapter(title="Front matter", start_page=0, level=1),
        Chapter(title="Chapter 1", start_page=1, level=1),
        Chapter(title="Back matter", start_page=2, level=1),
    ]
    page_texts = ["skip me", "keep me", "skip me too"]

    pages = paginate_chapters(
        page_texts, chapters, font_metrics=metrics, start_page=1, end_page=1
    )

    assert len(pages) == 1
    assert "keep me" in pages[0].lines[0]
    assert "skip" not in " ".join(pages[0].lines)


def test_paginate_chapters_sanity_word_count():
    # ~250 words/page * 200 pages ~= 50,000 words for a short novel
    # (acceptance criterion). Sanity-check the default font metrics land
    # in a reasonable ballpark, not an exact match.
    words = ["word"] * 50_000
    page_texts = [" ".join(words)]
    pages = paginate_chapters(page_texts, [], font_metrics=DEFAULT_FONT_METRICS)
    assert 100 <= len(pages) <= 400


def _make_pdf_with_toc(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "book.pdf"
    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text((50, 50), f"Chapter {i + 1} body text " * 50)
    doc.set_toc([[1, "Chapter 1", 1], [1, "Chapter 2", 2], [1, "Chapter 3", 3]])
    doc.save(str(pdf))
    doc.close()
    return pdf


def test_paginate_path_end_to_end(tmp_path):
    pdf = _make_pdf_with_toc(tmp_path)
    pages = paginate_path(pdf)
    assert len(pages) >= 1
    assert all(p.lines for p in pages)


def test_paginate_path_missing_pdf_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        paginate_path(tmp_path / "does-not-exist.pdf")


def test_cli_paginate_flag_logs_page_count(tmp_path, caplog):
    pdf = _make_pdf_with_toc(tmp_path)
    out = tmp_path / "out" / "book.txt"
    import logging

    with caplog.at_level(logging.INFO, logger="gbc_reader_prep"):
        assert main(["preprocess", str(pdf), "-o", str(out), "--paginate"]) == 0
    assert any("Pagination:" in r.message for r in caplog.records)


def test_cli_inspect_paginate_flag_logs_page_count_without_writing(tmp_path, caplog):
    pdf = _make_pdf_with_toc(tmp_path)
    import logging

    with caplog.at_level(logging.INFO, logger="gbc_reader_prep"):
        assert main(["preprocess", str(pdf), "--inspect", "--paginate"]) == 0
    assert any("Pagination:" in r.message for r in caplog.records)


def test_cli_paginate_with_custom_font_metrics(tmp_path, caplog):
    pdf = _make_pdf_with_toc(tmp_path)
    out = tmp_path / "out" / "book.txt"
    font_metrics_path = tmp_path / "font.json"
    font_metrics_path.write_text(json.dumps({"char_width_px": 8, "line_height_px": 16}))
    import logging

    with caplog.at_level(logging.INFO, logger="gbc_reader_prep"):
        assert main(
            [
                "preprocess",
                str(pdf),
                "-o",
                str(out),
                "--paginate",
                "--font-metrics",
                str(font_metrics_path),
            ]
        ) == 0
    assert any("Pagination:" in r.message for r in caplog.records)


def test_cli_paginate_output_writes_page_contents(tmp_path):
    pdf = _make_pdf_with_toc(tmp_path)
    out = tmp_path / "out" / "book.txt"
    dump = tmp_path / "out" / "pages.txt"

    assert main(
        [
            "preprocess",
            str(pdf),
            "-o",
            str(out),
            "--paginate",
            "--paginate-output",
            str(dump),
        ]
    ) == 0

    assert dump.exists()
    contents = dump.read_text(encoding="utf-8")
    assert "===== Page 1 (chapter 0: 'Chapter 1') =====" in contents
    assert "Chapter 1 body text" in contents


def test_cli_paginate_output_with_inspect(tmp_path):
    pdf = _make_pdf_with_toc(tmp_path)
    dump = tmp_path / "pages.txt"

    assert main(
        [
            "preprocess",
            str(pdf),
            "--inspect",
            "--paginate",
            "--paginate-output",
            str(dump),
        ]
    ) == 0
    assert dump.exists()


def test_cli_paginate_missing_font_metrics_returns_two(tmp_path):
    pdf = _make_pdf_with_toc(tmp_path)
    out = tmp_path / "out" / "book.txt"
    assert main(
        [
            "preprocess",
            str(pdf),
            "-o",
            str(out),
            "--paginate",
            "--font-metrics",
            str(tmp_path / "does-not-exist.json"),
        ]
    ) == 2
