"""Tests for ``gbc_reader_prep.trim``.

Refs: A-5
"""

from __future__ import annotations

import pytest

from gbc_reader_prep.chapters import Chapter
from gbc_reader_prep.trim import (
    TrimResult,
    detect_back_matter_chapter,
    detect_content_bounds,
)


def test_detect_back_matter_chapter_finds_appendix() -> None:
    chapters = [
        Chapter("Chapter 1", 0, 1),
        Chapter("Chapter 2", 10, 1),
        Chapter("Appendix A", 20, 1),
    ]
    assert detect_back_matter_chapter(chapters) == Chapter("Appendix A", 20, 1)


@pytest.mark.parametrize(
    "title",
    [
        "Notes",
        "Bibliography",
        "Index",
        "About the Author",
        "Acknowledgments",
        "Acknowledgements",
        "APPENDIX B",
    ],
)
def test_detect_back_matter_chapter_matches_known_titles(title: str) -> None:
    chapters = [Chapter("Chapter 1", 0, 1), Chapter(title, 5, 1)]
    match = detect_back_matter_chapter(chapters)
    assert match is not None
    assert match.title == title


def test_detect_back_matter_chapter_no_match() -> None:
    chapters = [Chapter("Chapter 1", 0, 1), Chapter("Chapter 2", 10, 1)]
    assert detect_back_matter_chapter(chapters) is None


def test_detect_back_matter_chapter_empty_input() -> None:
    assert detect_back_matter_chapter([]) is None


def test_detect_back_matter_chapter_picks_earliest_match() -> None:
    chapters = [
        Chapter("Chapter 1", 0, 1),
        Chapter("Index", 30, 1),
        Chapter("Appendix A", 20, 1),
    ]
    assert detect_back_matter_chapter(chapters).title == "Appendix A"


def test_detect_content_bounds_no_back_matter() -> None:
    chapters = [Chapter("Chapter 1", 2, 1), Chapter("Chapter 2", 10, 1)]
    result = detect_content_bounds(chapters, page_count=20)
    assert result == TrimResult(
        start_page=2,
        end_page=19,
        back_matter_title=None,
        back_matter_start_page=None,
    )


def test_detect_content_bounds_with_back_matter() -> None:
    chapters = [
        Chapter("Chapter 1", 2, 1),
        Chapter("Chapter 2", 10, 1),
        Chapter("Appendix A", 18, 1),
    ]
    result = detect_content_bounds(chapters, page_count=20)
    assert result == TrimResult(
        start_page=2,
        end_page=17,
        back_matter_title="Appendix A",
        back_matter_start_page=18,
    )


def test_detect_content_bounds_no_chapters() -> None:
    result = detect_content_bounds([], page_count=5)
    assert result == TrimResult(
        start_page=0,
        end_page=4,
        back_matter_title=None,
        back_matter_start_page=None,
    )


def test_detect_content_bounds_back_matter_is_first_chapter_is_ignored() -> None:
    """If the very first chapter looks like back matter (e.g. a heuristic
    false-positive), don't trim the entire book away."""
    chapters = [Chapter("Index", 0, 1)]
    result = detect_content_bounds(chapters, page_count=10)
    assert result == TrimResult(
        start_page=0,
        end_page=9,
        back_matter_title=None,
        back_matter_start_page=None,
    )


def test_detect_content_bounds_rejects_non_positive_page_count() -> None:
    with pytest.raises(ValueError):
        detect_content_bounds([], page_count=0)
