#!/usr/bin/env bash
# Import Chrome bookmarks from data/bookmarks/bookmarks.html (issue #1).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SHUTTLE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BOOKMARKS_FILE="${SHUTTLE_BOOKMARKS_FILE:-$ROOT/data/bookmarks/bookmarks.html}"
SKIP_AUTOMATION="${SHUTTLE_SKIP_CHROME_AUTOMATION:-0}"

if [[ ! -f "$BOOKMARKS_FILE" ]]; then
  echo "ERROR: Backup not found: $BOOKMARKS_FILE" >&2
  echo "Run export-bookmarks.sh first." >&2
  exit 1
fi

if [[ ! -s "$BOOKMARKS_FILE" ]]; then
  echo "ERROR: Backup file is empty: $BOOKMARKS_FILE" >&2
  exit 1
fi

run_chrome_import() {
  if [[ "$SKIP_AUTOMATION" == "1" ]]; then
    echo "Import ready: $BOOKMARKS_FILE (automation skipped)"
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
    echo "ERROR: Chrome import automation failed. Grant Accessibility permissions." >&2
    exit 1
  fi
  echo "Select backup file in Chrome: $BOOKMARKS_FILE"
}

run_chrome_import
echo "Import complete."
