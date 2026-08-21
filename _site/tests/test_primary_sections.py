"""Unit tests for primary-section navigation validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from check_primary_sections import find_mismatches  # noqa: E402


@pytest.fixture
def staged_case(tmp_path):
    def write(summary: str, pages: dict[str, tuple[str, str]]) -> tuple[Path, Path]:
        (tmp_path / "SUMMARY.md").write_text(summary, encoding="utf-8")
        for relative, (declared, body) in pages.items():
            page = tmp_path / relative
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(
                "---\n"
                f"description: Fixture page\nprimary_section: {declared}\n"
                "---\n\n"
                f"# {body}\n",
                encoding="utf-8",
            )
        return tmp_path, tmp_path / "SUMMARY.md"

    return write


def test_correctly_placed_page(staged_case):
    root, summary = staged_case(
        "## Marketing\n\n* [Reply workflow](marketing/replies.md)\n",
        {"marketing/replies.md": ("Marketing", "Reply workflow")},
    )

    assert find_mismatches(root, summary) == []


def test_page_beneath_wrong_top_level_section(staged_case):
    root, summary = staged_case(
        "## Vendor tools\n\n* [Build workflow](engineering/build.md)\n",
        {"engineering/build.md": ("Engineering", "Build workflow")},
    )

    mismatches = find_mismatches(root, summary)
    assert [m.describe() for m in mismatches] == [
        "engineering/build.md: declared 'Engineering', actual 'Vendor tools'"
    ]


def test_declared_page_missing_from_navigation(staged_case):
    root, summary = staged_case(
        "## Research\n\n* [Listed](research/listed.md)\n",
        {
            "research/listed.md": ("Research", "Listed"),
            "research/missing.md": ("Research", "Missing"),
        },
    )

    mismatches = find_mismatches(root, summary)
    assert [m.describe() for m in mismatches] == [
        "research/missing.md: declared 'Research', actual <missing from navigation>"
    ]


def test_section_names_with_punctuation_spaces_and_parentheses(staged_case):
    section = "Research, Analysis & Notes (Local)"
    root, summary = staged_case(
        f"## {section}\n\n* [Local review](research/local-review.md)\n",
        {"research/local-review.md": (f'"{section}"', "Local review")},
    )

    assert find_mismatches(root, summary) == []


def test_declared_page_cannot_have_two_primary_locations(staged_case):
    root, summary = staged_case(
        "## Marketing\n\n"
        "* [Shared workflow](workflows/shared.md)\n\n"
        "## Vendor tools\n\n"
        "* [Shared workflow](workflows/shared.md)\n",
        {"workflows/shared.md": ("Marketing", "Shared workflow")},
    )

    mismatches = find_mismatches(root, summary)
    assert [m.describe() for m in mismatches] == [
        "workflows/shared.md: declared 'Marketing', actual 'Marketing', 'Vendor tools'"
    ]
