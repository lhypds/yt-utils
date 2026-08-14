#!/usr/bin/env bash
# Preparation for ./install.sh: create .venv with Python >= 3.11, upgrade pip,
# seed the settings file in ~/.config/yt, check ffmpeg.
# Does not install project dependencies or the global yt command — run ./install.sh after this.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"

PY=""
for cmd in "${PYTHON:-}" python3.13 python3.12 python3.11 python3; do
    [ -z "$cmd" ] && continue
    command -v "$cmd" >/dev/null 2>&1 || continue
    if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
        PY="$cmd"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "error: need Python >= 3.11 for this project." >&2
    echo "  PYTHON=/opt/homebrew/bin/python3.12 ./setup.sh" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtualenv at $VENV_DIR ($PY)"
    "$PY" -m venv "$VENV_DIR"
else
    echo "==> Reusing existing virtualenv at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Upgrading pip"
pip install --upgrade pip

# Settings live in ~/.config/yt/.env so the installed `yt` finds its keys from
# any directory. A .env in this checkout still takes precedence, for development.
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/yt"
CONFIG_ENV="$CONFIG_DIR/.env"
if [ -f "$CONFIG_ENV" ]; then
    echo "==> Keeping existing $CONFIG_ENV"
else
    mkdir -p "$CONFIG_DIR"
    if [ -f ".env.example" ]; then
        cp ".env.example" "$CONFIG_ENV"
    else
        : >"$CONFIG_ENV"
    fi
    chmod 600 "$CONFIG_ENV"
    echo "==> Created $CONFIG_ENV"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
        echo "==> Installing ffmpeg via Homebrew"
        brew install ffmpeg
    elif command -v apt-get >/dev/null 2>&1; then
        echo "==> Installing ffmpeg via apt"
        sudo apt-get install -y ffmpeg
    else
        cat >&2 <<'EOF'

warning: ffmpeg was not found on PATH and no supported package manager detected.
  Install it manually:
    macOS:         brew install ffmpeg
    Debian/Ubuntu: sudo apt install ffmpeg
EOF
    fi
fi

cat <<EOF

Setup complete — ready for ./install.sh

Next step (installs Python deps + global \`yt\` command):
    ./install.sh

API keys go in $CONFIG_ENV (OPENAI_API_KEY).
\`yt\` asks for it the first time it needs it.

Optional: activate the venv only (no global \`yt\` yet):
    source $VENV_DIR/bin/activate
EOF
