#!/usr/bin/env bash
# Build the site and publish it to Cloudflare Pages.
#
# This exists because Cloudflare cannot watch the GitHub repo while the GitHub
# account is flagged. It uploads straight from this machine instead, so no
# GitHub App is involved. When GitHub is unblocked, connect the repo in the
# Cloudflare dashboard and this script becomes optional.
#
# Needs two values, read from _site/.env (which is gitignored):
#   CLOUDFLARE_API_TOKEN   created in the Cloudflare dashboard
#   CLOUDFLARE_ACCOUNT_ID  the long id in your dashboard URL
#
#   bash deploy.sh
set -euo pipefail

cd "$(dirname "$0")"

PROJECT="${PROJECT:-3rdbrain}"
# Anything other than the project's production branch publishes as a preview
# deployment, which is the only kind Cloudflare Access can protect.
BRANCH="${BRANCH:-main}"

if [ -f .env ]; then
  # Strip CR left by Windows editors; CR-tainted values are not inherited
  # reliably by Windows executables launched from Git Bash.
  while IFS='=' read -r key value || [ -n "${key:-}" ]; do
    key="${key%$'\r'}"
    value="${value%$'\r'}"
    case "$key" in
      ''|'#'*) continue ;;
      CLOUDFLARE_API_TOKEN|CLOUDFLARE_ACCOUNT_ID|SITE_PASSWORD)
        printf -v "$key" '%s' "$value"
        export "$key"
        ;;
    esac
  done < .env
fi

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ] || [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  echo "deploy: missing credentials. Create _site/.env with:"
  echo "  CLOUDFLARE_API_TOKEN=..."
  echo "  CLOUDFLARE_ACCOUNT_ID=..."
  exit 1
fi

# One deploy at a time. The content pipeline can make several commits in a run,
# and there is no value in racing three uploads against each other.
LOCK=".deploy.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "deploy: another deploy is already running; skipping"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

PYTHON="${PYTHON:-.venv/Scripts/python.exe}"
VAULT=.. PYTHON="$PYTHON" SITE_PASSWORD="${SITE_PASSWORD:-}" bash build.sh

if command -v node >/dev/null 2>&1; then
  ./node_modules/.bin/wrangler pages deploy site \
    --project-name "$PROJECT" \
    --branch "$BRANCH" \
    --commit-dirty=true
elif command -v powershell.exe >/dev/null 2>&1 && [ -f ./node_modules/.bin/wrangler.cmd ]; then
  # Git Bash may not inherit the Windows Node installation on PATH. Invoke the
  # Windows shim through PowerShell so post-commit deployments still work.
  powershell.exe -NoProfile -Command \
    "& './node_modules/.bin/wrangler.cmd' pages deploy site --project-name '$PROJECT' --branch '$BRANCH' --commit-dirty=true"
else
  echo "deploy: Wrangler cannot start; Node.js is not available"
  exit 1
fi

"$PYTHON" tools/verify_deployment_manifest.py site "$PROJECT" "$BRANCH"

echo "deploy: deployment and exact-case manifest verified"
