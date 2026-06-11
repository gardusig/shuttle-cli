#!/usr/bin/env bash
# Install shuttle CLI into ~/.local/bin (macOS-friendly)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${SHUTTLE_INSTALL_DIR:-$HOME/.local/bin}"
VENV="$ROOT/.venv"

if [[ ! -d "$VENV" ]]; then
  echo "Running bootstrap first..."
  "$ROOT/scripts/bootstrap.sh"
fi

mkdir -p "$DEST"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -e "$ROOT" -q

cat >"$DEST/shuttle" <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" -m shuttle "\$@"
EOF
chmod +x "$DEST/shuttle"

echo "Installed: $DEST/shuttle"
echo "Ensure $DEST is on your PATH."
