"""Validate declared primary sections against staged SUMMARY navigation.

Pages opt in by declaring ``primary_section`` in YAML frontmatter. Every
declaring page must appear under exactly that top-level ``##`` section in the
staged SUMMARY.md. Legacy pages without the field remain valid.

    python tools/check_primary_sections.py .build .build/SUMMARY.md
"""

from __future__ import annotations

import posixpath
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+(?P<section>.+?)\s*$")
LINK_RE = re.compile(
    r"^\s*\*\s+\[[^]]+\]\((?P<target>.+?\.md)(?:[?#][^)]*)?\)(?:\s|$)"
)
PRIMARY_SECTION_RE = re.compile(r"^primary_section:\s*(?P<value>.+?)\s*$", re.M)
EXCLUDED_PAGES = {"SUMMARY.md", "NAV.md", "NAV-EXTRA.md"}


@dataclass(frozen=True)
class PrimarySectionMismatch:
    page: str
    declared: str
    actual: tuple[str, ...]

    def describe(self) -> str:
        actual = ", ".join(repr(section) for section in self.actual)
        if not actual:
            actual = "<missing from navigation>"
        return f"{self.page}: declared {self.declared!r}, actual {actual}"


def normalize_target(target: str) -> str:
    """Return a SUMMARY target in the same form as Path.as_posix()."""
    decoded = urllib.parse.unquote(target).replace("\\", "/").strip("<>")
    normalized = posixpath.normpath(decoded)
    return normalized.removeprefix("./")


def summary_placements(summary_text: str) -> dict[str, set[str]]:
    """Map each linked Markdown page to its top-level SUMMARY section(s)."""
    section: str | None = None
    placed: dict[str, set[str]] = {}
    for line in summary_text.splitlines():
        heading = SECTION_RE.match(line)
        if heading:
            section = heading.group("section").strip()
            continue

        link = LINK_RE.match(line)
        if link and section:
            target = normalize_target(link.group("target"))
            placed.setdefault(target, set()).add(section)
    return placed


def declared_primary_section(page_text: str) -> str | None:
    """Read primary_section only from the opening YAML frontmatter block."""
    lines = page_text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    try:
        closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None

    match = PRIMARY_SECTION_RE.search("\n".join(lines[1:closing]))
    if not match:
        return None
    value = match.group("value").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


def find_mismatches(staged_root: Path, summary_path: Path) -> list[PrimarySectionMismatch]:
    """Return every missing or incorrectly placed declaring page."""
    placements = summary_placements(summary_path.read_text(encoding="utf-8-sig"))
    mismatches: list[PrimarySectionMismatch] = []

    for page in sorted(staged_root.rglob("*.md")):
        if page.name in EXCLUDED_PAGES:
            continue
        declared = declared_primary_section(page.read_text(encoding="utf-8-sig"))
        if declared is None:
            continue

        relative = page.relative_to(staged_root).as_posix()
        actual = tuple(sorted(placements.get(relative, set())))
        if actual != (declared,):
            mismatches.append(PrimarySectionMismatch(relative, declared, actual))

    return mismatches


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    staged_root = Path(sys.argv[1])
    summary_path = Path(sys.argv[2])
    mismatches = find_mismatches(staged_root, summary_path)
    if mismatches:
        print("primary navigation section mismatch:")
        for mismatch in mismatches:
            print("  " + mismatch.describe())
        return 1
    print("primary navigation sections: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
