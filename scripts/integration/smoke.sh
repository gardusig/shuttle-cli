#!/usr/bin/env bash
# Integration smoke (container only — invoked by scripts/docker/run-integration.sh).
set -euo pipefail

ROOT="${SHUTTLE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$ROOT"

python -m shuttle --help >/dev/null
python -m shuttle --version | grep -q "0.1.0"

python -m shuttle backup | grep -q "backup: not implemented yet"
python -m shuttle restore | grep -q "restore: not implemented yet"
python -m shuttle drives | grep -q "drives: not implemented yet"
python -m shuttle notion | grep -q "notion: not implemented yet"
python -m shuttle bookmarks | grep -q "scripts/chrome/export-bookmarks.sh"

links_out="$(mktemp)"
python -m shuttle links >"$links_out" 2>&1
grep -q "Quick defaults" "$links_out"
rm -f "$links_out"

bash -n scripts/bootstrap.sh scripts/install.sh
bash -n scripts/chrome/*.sh
bash -n scripts/git/*.sh
bash -n scripts/integration/*.sh

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

downloads="$tmpdir/Downloads"
bookmarks_dir="$tmpdir/data/bookmarks"
mkdir -p "$downloads" "$bookmarks_dir"

cp tests/fixtures/bookmarks.html "$downloads/bookmarks.html"

SHUTTLE_ROOT="$tmpdir" \
SHUTTLE_DOWNLOADS_DIR="$downloads" \
SHUTTLE_BOOKMARKS_FILE="$bookmarks_dir/bookmarks.html" \
SHUTTLE_SKIP_CHROME_AUTOMATION=1 \
scripts/chrome/export-bookmarks.sh

test -s "$bookmarks_dir/bookmarks.html"
grep -q "Shuttle Test Bookmark" "$bookmarks_dir/bookmarks.html"

SHUTTLE_ROOT="$tmpdir" \
SHUTTLE_BOOKMARKS_FILE="$bookmarks_dir/bookmarks.html" \
SHUTTLE_SKIP_CHROME_AUTOMATION=1 \
scripts/chrome/import-bookmarks.sh | grep -q "Import complete"

git init -b main "$tmpdir/repo" >/dev/null
git -C "$tmpdir/repo" config user.email "shuttle@example.test"
git -C "$tmpdir/repo" config user.name "Shuttle Test"
touch "$tmpdir/repo/README.md"
git -C "$tmpdir/repo" add README.md
git -C "$tmpdir/repo" commit -m "initial" >/dev/null

(
  cd "$tmpdir/repo"
  python -m shuttle git start smoke-branch --no-prep | grep -q "smoke-branch"
  test "$(git branch --show-current)" = "smoke-branch"
)

python scripts/integration/check_public_commands.py
python scripts/integration/check_workflow_integration.py

echo "Docker integration smoke passed."
