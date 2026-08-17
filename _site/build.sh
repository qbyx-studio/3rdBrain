#!/usr/bin/env bash
# Build the private site from the GitBook-synced content repo.
#
# The content in vault/ is owned by GitBook and must never be modified: GitBook
# syncs it bidirectionally, so a write here would fight the sync. Every
# transformation therefore runs against an ephemeral copy in .build/, which is
# regenerated from scratch on each run and is not committed.
#
#   vault/    untouched mirror of the content repo (CI checkout in production)
#   overlay/  files this site adds that GitBook does not know about
#   .build/   vault + overlay + transforms, thrown away and rebuilt each time
#
#   PYTHON=.venv/Scripts/python.exe bash build.sh
set -euo pipefail

# Find or create the virtual environment. The interpreter lives in a different
# place on Windows than everywhere else, so detect it rather than assume.
find_python() {
  if [ -n "${PYTHON:-}" ] && [ -x "${PYTHON}" ]; then echo "$PYTHON"; return; fi
  if [ -x ".venv/bin/python" ]; then echo ".venv/bin/python"; return; fi
  if [ -x ".venv/Scripts/python.exe" ]; then echo ".venv/Scripts/python.exe"; return; fi
  echo ""
}

PYTHON="$(find_python)"

if [ -z "$PYTHON" ]; then
  echo "creating virtual environment..."
  if command -v uv >/dev/null 2>&1; then
    uv venv .venv >/dev/null
  else
    BASE_PY="$(command -v python3 || command -v python || true)"
    if [ -z "$BASE_PY" ]; then
      echo "Python 3.10 or newer is required. Install it, then run this again." >&2
      exit 1
    fi
    "$BASE_PY" -m venv .venv 2>/dev/null || {
      echo "Could not create a virtual environment." >&2
      echo "On Debian or Ubuntu: sudo apt install python3-venv python3-pip" >&2
      exit 1
    }
  fi
  PYTHON="$(find_python)"
fi

if [ -z "$PYTHON" ]; then
  echo "Virtual environment created but no interpreter found inside it." >&2
  exit 1
fi

# Install dependencies. uv is fastest when present. Otherwise use pip, and
# bootstrap it first if the distribution shipped a venv without one, which is
# the default on Debian and Ubuntu.
if command -v uv >/dev/null 2>&1; then
  uv pip install --quiet --python "$PYTHON" -r requirements.txt
else
  if ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
    "$PYTHON" -m ensurepip --upgrade >/dev/null 2>&1 || {
      echo "This Python has no pip and cannot bootstrap one." >&2
      echo "On Debian or Ubuntu: sudo apt install python3-pip python3-venv" >&2
      exit 1
    }
  fi
  "$PYTHON" -m pip install --quiet --upgrade pip
  "$PYTHON" -m pip install --quiet -r requirements.txt
fi

echo "staging..."
rm -rf .build
# Python rather than cp: when the site lives inside the content repo (VAULT=..)
# a plain copy would recurse into its own output. This skips the site folder,
# git metadata and build artefacts, and keeps dotfiles like .gitbook/assets.
"$PYTHON" - "$VAULT" <<'STAGE'
import shutil, sys
from pathlib import Path

vault = Path(sys.argv[1]).resolve()
here = Path.cwd().resolve()
skip = {".git", ".github", ".venv", ".build", "site", "__pycache__", "node_modules"}
if here.parent == vault or here.is_relative_to(vault):
    skip.add(here.name)          # never copy the build folder into itself

def ignore(directory, names):
    d = Path(directory).resolve()
    return {n for n in names if n in skip and (d != vault or n != "site" or True)}

shutil.copytree(vault, here / ".build", ignore=ignore, dirs_exist_ok=True)
shutil.copytree(here / "overlay", here / ".build", dirs_exist_ok=True)
print(f"  staged from {vault}")
STAGE

# Derived, not authored: tags come from each page's **Facets:** footer, so no
# page has to be hand-tagged and the vault keeps its existing convention.
"$PYTHON" tools/facets_to_tags.py .build | tail -1

# Relevance tuning: boost hub pages, drop the redundant facet hubs from the
# index. Derived at build time, so the vault stays untouched.
"$PYTHON" tools/search_tuning.py .build

# GitBook sections -> literate-nav nesting.
"$PYTHON" tools/summary_to_nav.py .build/SUMMARY.md .build/NAV.md

# Not --strict: the pinned toolchain emits its own deprecation warnings, which
# strict mode would treat as build failures. Link validation lives in mkdocs.yml.
"$PYTHON" -m mkdocs build --clean

# Regression gate. Each test corresponds to a bug that actually shipped
# during the migration. Set SKIP_TESTS=1 to bypass.
if [ -z "${SKIP_TESTS:-}" ] && "$PYTHON" -m pytest --version >/dev/null 2>&1; then
  # Build integrity: a failure here means the site is wrong, so stop.
  "$PYTHON" -m pytest tests -q -m "not content"

  # Content quality: broken links and the like. Reported, never fatal - the
  # content pipeline is often mid-run, and a stale link must not stop a deploy.
  if ! "$PYTHON" -m pytest tests -q -m content; then
    echo "  ^ content warnings above; publishing anyway"
  fi
fi

echo "built -> site/"
