"""GitBook-compatible heading slugs.

GitBook is the source of truth and every in-page anchor in the base was written
against its rules. Python-Markdown slugifies differently, so anchors that are
correct in GitBook break here. Rather than rewrite the content (which would
break it in GitBook), the renderer is taught GitBook's rule.

The difference that matters: GitBook maps *each* whitespace character to a
separator and drops other punctuation, so "manager + Brock's" becomes
"manager--brocks" - two dashes, because the '+' vanishes and both spaces
survive. Python-Markdown collapses whitespace runs into one separator and
produces "manager-brocks".
"""

from __future__ import annotations

import re
import unicodedata

_KEEP = re.compile(r"[^\w\s-]", re.UNICODE)


def slugify(value: str, separator: str = "-") -> str:
    """Slugify a heading the way GitBook does."""
    # Normalise so accented characters reduce to their base letter.
    value = unicodedata.normalize("NFKD", str(value))
    value = value.lower()
    # Drop punctuation, but leave whitespace in place so each space still
    # becomes its own separator.
    value = _KEEP.sub("", value)
    # One separator per whitespace character, not per run.
    value = re.sub(r"\s", separator, value)
    return value.strip(separator)
