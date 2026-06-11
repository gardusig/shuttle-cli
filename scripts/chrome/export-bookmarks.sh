#!/usr/bin/env bash
# Export Chrome bookmarks to data/bookmarks/bookmarks.html (issue #1).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
DOWNLOADS_DIR="${SHUTTLE_DOWNLOADS_DIR:-$HOME/Downloads}"
BOOKMARKS_FILE="${SHUTTLE_BOOKMARKS_FILE:-$ROOT/data/bookmarks/bookmarks.html}"
SKIP_AUTOMATION="${SHUTTLE_SKIP_CHROME_AUTOMATION:-0}"
FIXTURE_SOURCE="${SHUTTLE_BOOKMARKS_FIXTURE:-}"

mkdir -p "$(dirname "$BOOKMARKS_FILE")"

run_chrome_export() {
  if [[ "$SKIP_AUTOMATION" == "1" ]]; then
    return 0
  fi
  if ! command -v osascript >/dev/null 2>&1; then
    echo "ERROR: osascript not found (macOS required)" >&2
    exit 1
  fi
  open -a "Google Chrome" "chrome://bookmarks" 2>/dev/null || open -a "Google Chrome"
  sleep 2
  if ! osascript <<'APPLESCRIPT'
tell application "Google Chrome" to activate
delay 1
tell application "System Events"
  tell process "Google Chrome"
    keystroke "o" using {command down, shift down}
  end tell
end tell
APPLESCRIPT
  then
    echo "ERROR: Chrome export automation failed. Grant Accessibility permissions." >&2
    exit 1
  fi
}

resolve_download() {
  if [[ -n "$FIXTURE_SOURCE" ]]; then
    if [[ ! -f "$FIXTURE_SOURCE" ]]; then
      echo "ERROR: Fixture source not found: $FIXTURE_SOURCE" >&2
      exit 1
    fi
    printf '%s\n' "$FIXTURE_SOURCE"
    return 0
  fi
  if [[ "$SKIP_AUTOMATION" != "1" ]]; then
    SINCE_EPOCH=$(date +%s)
    export SHUTTLE_DOWNLOAD_SINCE_EPOCH="$SINCE_EPOCH"
  fi
  "$SCRIPT_DIR/wait-download.sh"
}

install_backup() {
  local src="$1"
  local tmp="${BOOKMARKS_FILE}.tmp.$$"
  cp "$src" "$tmp"
  mv -f "$tmp" "$BOOKMARKS_FILE"
  echo "Exported bookmarks to $BOOKMARKS_FILE"
}

run_chrome_export
downloaded=$(resolve_download)
install_backup "$downloaded"

if [[ -z "$FIXTURE_SOURCE" && "$downloaded" == "$DOWNLOADS_DIR"/* ]]; then
  rm -f "$downloaded"
fi
