"""Smoke tests for the CLI skeleton.

Ticket: A-1.
"""

from __future__ import annotations

import subprocess

import pytest

from gbc_reader_prep import __version__
from gbc_reader_prep.cli import build_parser, main


def test_version_string_present() -> None:
    assert isinstance(__version__, str) and __version__


def test_parser_accepts_version_flag() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])
    # argparse exits with code 0 after printing version
    assert exc_info.value.code == 0


def test_main_default_invocation_returns_zero() -> None:
    assert main([]) == 0


def test_console_script_reports_version() -> None:
    """The installed console script must run and report a version."""
    result = subprocess.run(
        ["gbc-reader-prep", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert __version__ in combined
    assert "gbc-reader-prep" in combined

def test_preprocess_help_runs(capsys):
    """`gbc-reader-prep preprocess --help` exits 0 and mentions 'preprocess'."""
    with pytest.raises(SystemExit) as exc_info:
        main(["preprocess", "--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "preprocess" in out.lower()


def test_preprocess_requires_output_without_inspect(tmp_path, caplog):
    """A-5: -o/--output is required unless --inspect is given."""
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "book.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(pdf))
    doc.close()

    assert main(["preprocess", str(pdf)]) == 2
    assert "output" in caplog.text.lower()


def test_preprocess_inspect_reports_proposed_bounds(tmp_path, caplog):
    """A-5: --inspect prints a dry-run report and writes no output file."""
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "book.pdf"
    doc = pymupdf.open()
    for _ in range(5):
        doc.new_page()
    doc.set_toc([[1, "Chapter 1", 1], [1, "Appendix A", 4]])
    doc.save(str(pdf))
    doc.close()

    caplog.set_level("INFO", logger="gbc_reader_prep")
    assert main(["preprocess", str(pdf), "--inspect"]) == 0
    assert "Proposed main content: pages 1-3" in caplog.text
    assert "Appendix A" in caplog.text
    assert not (tmp_path / "book.txt").exists()


def test_preprocess_inspect_missing_pdf_returns_two(tmp_path):
    missing = tmp_path / "does-not-exist.pdf"
    assert main(["preprocess", str(missing), "--inspect"]) == 2


def test_preprocess_inspect_respects_start_end_page_overrides(tmp_path, caplog):
    """A-5: --start-page/--end-page override auto-detected bounds."""
    pymupdf = pytest.importorskip("pymupdf")
    pdf = tmp_path / "book.pdf"
    doc = pymupdf.open()
    for _ in range(5):
        doc.new_page()
    doc.set_toc([[1, "Chapter 1", 1], [1, "Appendix A", 4]])
    doc.save(str(pdf))
    doc.close()

    caplog.set_level("INFO", logger="gbc_reader_prep")
    assert (
        main(
            [
                "preprocess",
                str(pdf),
                "--inspect",
                "--start-page",
                "1",
                "--end-page",
                "4",
            ]
        )
        == 0
    )
    assert "Proposed main content: pages 2-5" in caplog.text
    assert "overridden via --start-page" in caplog.text
    assert "overridden via --end-page" in caplog.text
