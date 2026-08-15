#!/usr/bin/env bash
# Preparation for ./install.sh: create .venv with Python >= 3.11, upgrade pip,
# seed the settings file in ~/.config/yt, check ffmpeg.
# Does not install project dependencies or the global yt command — run ./install.sh after this.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"

CANDIDATES="python3.13 python3.12 python3.11 python3 python"

PY=""
# Plain `python` is probed too: on pyenv, conda and python-is-python3 machines it
# is often the only name that exists.
for cmd in "${PYTHON:-}" $CANDIDATES; do
    [ -z "$cmd" ] && continue
    command -v "$cmd" >/dev/null 2>&1 || continue
    if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
        # Keep the interpreter itself, not the name that found it. A pyenv or asdf
        # shim picks its version from a .python-version found by walking up from
        # the working directory, so the same name means different interpreters in
        # different places — and this script has already cd'd into ROOT_DIR.
        PY="$("$cmd" -c 'import sys; print(sys.executable)' 2>/dev/null)"
        [ -n "$PY" ] || PY="$cmd"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "error: need Python >= 3.11 for this project, and none of these is:" >&2
    for cmd in $CANDIDATES; do
        command -v "$cmd" >/dev/null 2>&1 || continue
        echo "    $cmd -> $("$cmd" --version 2>&1 | head -1)" >&2
    done
    if [ -f "$ROOT_DIR/.python-version" ]; then
        echo "  Note: $ROOT_DIR/.python-version pins them all to \
$(tr -d '[:space:]' < "$ROOT_DIR/.python-version") in this directory. Delete it if it is not yours." >&2
    fi
    echo "  Or point at one directly:  PYTHON=/usr/bin/python3.12 ./setup.sh" >&2
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
