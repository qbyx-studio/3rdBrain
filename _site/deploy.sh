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

PROJECT="${PROJECT:-promptos}"
# Anything other than the project's production branch publishes as a preview
# deployment, which is the only kind Cloudflare Access can protect.
BRANCH="${BRANCH:-main}"

[ -f .env ] && set -a && . ./.env && set +a

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

./node_modules/.bin/wrangler pages deploy site \
  --project-name "$PROJECT" \
  --branch "$BRANCH" \
  --commit-dirty=true

"$PYTHON" tools/verify_deployment_manifest.py site "$PROJECT" "$BRANCH"

echo "deploy: done -> https://${BRANCH}.${PROJECT}.pages.dev"
