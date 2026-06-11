#!/usr/bin/env bash
# Poll Downloads for the newest completed .html file (issue #1).
set -euo pipefail

DOWNLOADS_DIR="${SHUTTLE_DOWNLOADS_DIR:-$HOME/Downloads}"
TIMEOUT="${SHUTTLE_DOWNLOAD_TIMEOUT:-120}"
INTERVAL="${SHUTTLE_DOWNLOAD_INTERVAL:-1}"
SINCE_EPOCH="${SHUTTLE_DOWNLOAD_SINCE_EPOCH:-}"

if [[ ! -d "$DOWNLOADS_DIR" ]]; then
  echo "ERROR: Downloads directory not found: $DOWNLOADS_DIR" >&2
  exit 1
fi

file_mtime() {
  local path="$1" value=""
  value=$(stat -f "%m" "$path" 2>/dev/null || true)
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$value"
    return 0
  fi
  value=$(stat -c "%Y" "$path" 2>/dev/null || true)
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$value"
    return 0
  fi
  printf '0\n'
}

find_newest_html() {
  local newest="" newest_mtime=0 mtime path
  while IFS= read -r -d '' path; do
    [[ "$path" == *.crdownload ]] && continue
    mtime=$(file_mtime "$path")
    if [[ -n "$SINCE_EPOCH" && "$mtime" -le "$SINCE_EPOCH" ]]; then
      continue
    fi
    if [[ "$mtime" -gt "$newest_mtime" ]]; then
      newest_mtime=$mtime
      newest=$path
    fi
  done < <(find "$DOWNLOADS_DIR" -maxdepth 1 -type f -name '*.html' -print0 2>/dev/null)
  if [[ -n "$newest" ]]; then
    printf '%s\n' "$newest"
    return 0
  fi
  return 1
}

elapsed=0
while [[ "$elapsed" -lt "$TIMEOUT" ]]; do
  if result=$(find_newest_html); then
    printf '%s\n' "$result"
    exit 0
  fi
  sleep "$INTERVAL"
  elapsed=$((elapsed + INTERVAL))
done

echo "ERROR: Timed out after ${TIMEOUT}s waiting for HTML download in $DOWNLOADS_DIR" >&2
exit 1
