#!/usr/bin/env bash
# Remove the global yt launcher installed by ./install.sh for this repo.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LAUNCHER_DIR="$HOME/.local/bin"
LAUNCHER="$LAUNCHER_DIR/yt"
MARKER="# yt-launcher:REPO=$ROOT_DIR"

if [ -f "$LAUNCHER" ] && grep -qF "$MARKER" "$LAUNCHER"; then
    echo "==> Removing $LAUNCHER"
    rm "$LAUNCHER"
else
    if [ -f "$LAUNCHER" ]; then
        echo "warning: $LAUNCHER exists but is not this repo's launcher; left unchanged." >&2
    else
        echo "(no launcher at $LAUNCHER)"
    fi
fi

cat <<EOF

To remove the virtualenv and all installed wheels:
    rm -rf $ROOT_DIR/.venv

Settings (API keys) are left alone. To remove them too:
    rm -rf ${XDG_CONFIG_HOME:-$HOME/.config}/yt
EOF
