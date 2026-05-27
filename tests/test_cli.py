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
