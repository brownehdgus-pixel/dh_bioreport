#!/usr/bin/env bash
# Vercel ignoreCommand: exit 0 = skip build, exit 1 = build
# Skip when ONLY data/crawl_config.json changed (Next.js does not import it at build time).

set -euo pipefail

PREV="${VERCEL_GIT_PREVIOUS_SHA:-}"
CURR="${VERCEL_GIT_COMMIT_SHA:-}"

if [ -z "$PREV" ] || [ -z "$CURR" ]; then
  exit 1
fi

CHANGED="$(git diff --name-only "$PREV" "$CURR" || true)"

if [ -z "$CHANGED" ]; then
  exit 1
fi

ONLY_CONFIG=true
while IFS= read -r file; do
  [ -z "$file" ] && continue
  if [ "$file" != "data/crawl_config.json" ]; then
    ONLY_CONFIG=false
    break
  fi
done <<< "$CHANGED"

if [ "$ONLY_CONFIG" = true ]; then
  echo "Only crawl_config.json changed — skipping build"
  exit 0
fi

exit 1
