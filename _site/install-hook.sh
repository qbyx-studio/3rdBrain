#!/usr/bin/env bash
# Install the hooks that publish the site whenever content changes.
# Git hooks are not version-controlled, so this copies them into place.
#
#   bash _site/install-hook.sh
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT/_site/git-hooks/deploy-trigger"

for hook in post-commit post-merge post-rewrite; do
  DEST="$ROOT/.git/hooks/$hook"
  if [ -e "$DEST" ] && ! grep -q "deploy.sh" "$DEST" 2>/dev/null; then
    cp "$DEST" "$DEST.backup"
    echo "  existing $hook backed up"
  fi
  cp "$SRC" "$DEST"
  chmod +x "$DEST"
  echo "  installed $hook"
done

echo
echo "The site now republishes after a commit, a pull, or a rebase."
