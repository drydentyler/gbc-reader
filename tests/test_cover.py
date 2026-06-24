"""Tests for cover image extraction.

Ticket: A-6.
"""

from __future__ import annotations

import base64

import pytest

from gbc_reader_prep.cli import main
from gbc_reader_prep.cover import (
    COVER_HEIGHT,
    COVER_WIDTH,
    cover_to_base64,
    extract_cover,
    render_cover,
)


def _make_pdf(tmp_path, pages: int = 1):
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "book.pdf"
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((50, 50), "Cover Title", fontsize=24)
    doc.save(str(pdf))
    doc.close()
    return pdf


def test_render_cover_returns_1bit_image_at_target_size(tmp_path):
    pdf = _make_pdf(tmp_path)
    image = render_cover(pdf)
    assert image.mode == "1"
    assert image.size == (COVER_WIDTH, COVER_HEIGHT)


def test_render_cover_missing_pdf_raises(tmp_path):
    missing = tmp_path / "does-not-exist.pdf"
    with pytest.raises(FileNotFoundError):
        render_cover(missing)


def test_cover_to_base64_round_trips_as_valid_png(tmp_path):
    pdf = _make_pdf(tmp_path)
    image = render_cover(pdf)
    encoded = cover_to_base64(image)
    decoded = base64.b64decode(encoded)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


def test_extract_cover_saves_png_and_returns_base64(tmp_path):
    pdf = _make_pdf(tmp_path)
    out_dir = tmp_path / "out"
    cover_path, encoded = extract_cover(pdf, out_dir)

    assert cover_path == out_dir / "cover.png"
    assert cover_path.exists()
    assert cover_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert base64.b64decode(encoded) == cover_path.read_bytes()


def test_preprocess_extract_cover_flag_saves_cover(tmp_path):
    pdf = _make_pdf(tmp_path)
    out = tmp_path / "out" / "book.txt"

    assert main(
        ["preprocess", str(pdf), "-o", str(out), "--extract-cover"]
    ) == 0
    assert out.exists()
    assert (out.parent / "cover.png").exists()


def test_preprocess_extract_cover_missing_pdf_returns_two(tmp_path):
    missing = tmp_path / "does-not-exist.pdf"
    out = tmp_path / "out" / "book.txt"
    # extract_text will already fail with 2 before cover extraction runs.
    assert main(
        ["preprocess", str(missing), "-o", str(out), "--extract-cover"]
    ) == 2
