#!/usr/bin/env bash
# One-command installer for `yt` on Linux and macOS:
#
#   curl -fsSL https://raw.githubusercontent.com/lhypds/yt/master/get.sh | bash
#
# Downloads a release zip from GitHub, unpacks it into ~/.yt, then runs the
# shipped setup.sh and install.sh — which build the venv, check for ffmpeg,
# install the Python dependencies, and write the ~/.local/bin/yt launcher.
#
# Options (flag or environment variable):
#   --version 0.0.11  YT_VERSION=0.0.11  install a specific release (default: latest)
#   --dir PATH        YT_HOME=PATH       where to unpack (default: ~/.yt)
#   --help
#
# Re-running upgrades in place: the existing .venv and .env are kept.
set -euo pipefail

NAME="yt"
REPO="lhypds/yt"
INSTALL_DIR="${YT_HOME:-$HOME/.$NAME}"
VERSION="${YT_VERSION:-}"

usage() {
    cat <<EOF
Install the $NAME command (Linux and macOS).

Usage:
    curl -fsSL https://raw.githubusercontent.com/$REPO/master/get.sh | bash
    curl -fsSL https://raw.githubusercontent.com/$REPO/master/get.sh | bash -s -- --version 0.0.11

Options:
    --version VERSION   release to install, e.g. 0.0.11 (default: latest)
    --dir PATH          where to unpack (default: \$HOME/.$NAME)
    -h, --help          show this message
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --version) VERSION="${2:-}"; shift 2 ;;
        --version=*) VERSION="${1#*=}"; shift ;;
        --dir) INSTALL_DIR="${2:-}"; shift 2 ;;
        --dir=*) INSTALL_DIR="${1#*=}"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "error: unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
done

[ -n "$INSTALL_DIR" ] || { echo "error: --dir needs a path." >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

# Unpacking over a checkout would overwrite tracked files with release copies.
if [ -e "$INSTALL_DIR/.git" ]; then
    echo "error: $INSTALL_DIR is a git checkout — get.sh would overwrite it." >&2
    echo "  Install elsewhere with --dir PATH, or from inside the checkout run:" >&2
    echo "      ./setup.sh && ./install.sh" >&2
    exit 1
fi

OS="$(uname -s)"
case "$OS" in
    Linux|Darwin) ;;
    *)
        echo "error: get.sh supports Linux and macOS only (found: $OS)." >&2
        echo "  On Windows, use WSL or install from source: https://github.com/$REPO" >&2
        exit 1
        ;;
esac

if have curl; then
    fetch_stdout() { curl -fsSL "$1"; }
    fetch_file() { curl -fsSL --retry 2 -o "$2" "$1"; }
elif have wget; then
    fetch_stdout() { wget -qO- "$1"; }
    fetch_file() { wget -q -O "$2" "$1"; }
else
    echo "error: need curl or wget to download the release." >&2
    exit 1
fi

# Pick the interpreter here rather than leaving it to setup.sh, so a machine
# without a usable Python fails before anything is downloaded or written.
PY=""
for cmd in "${PYTHON:-}" python3.13 python3.12 python3.11 python3; do
    [ -z "$cmd" ] && continue
    have "$cmd" || continue
    if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
        PY="$cmd"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "error: need Python >= 3.11 for $NAME." >&2
    if [ "$OS" = "Darwin" ]; then
        echo "  brew install python@3.12" >&2
    else
        echo "  sudo apt install python3.12 python3.12-venv   # Debian/Ubuntu" >&2
        echo "  sudo dnf install python3.12                   # Fedora" >&2
    fi
    echo "  Already installed elsewhere? PYTHON=/path/to/python3.12 bash get.sh" >&2
    exit 1
fi
export PYTHON="$PY"

# Latest release: read the tag from where /releases/latest redirects (no API
# rate limit), and fall back to the API when that is unavailable.
resolve_latest() {
    local url tag
    if have curl; then
        url="$(curl -fsSLI -o /dev/null -w '%{url_effective}' \
            "https://github.com/$REPO/releases/latest" 2>/dev/null || true)"
        tag="${url##*/}"
        case "$tag" in
            v[0-9]*) printf '%s' "${tag#v}"; return 0 ;;
        esac
    fi
    tag="$(fetch_stdout "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null |
        grep -m1 '"tag_name"' |
        sed -E 's/.*"tag_name"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)"
    [ -n "$tag" ] && printf '%s' "${tag#v}"
}

if [ -z "$VERSION" ]; then
    echo "==> Looking up the latest $NAME release"
    VERSION="$(resolve_latest)"
    if [ -z "$VERSION" ]; then
        echo "error: could not determine the latest release of $REPO." >&2
        echo "  Pick one manually: bash get.sh --version 0.0.11" >&2
        exit 1
    fi
fi
VERSION="${VERSION#v}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ZIP_NAME="${NAME}_v${VERSION}.zip"
ZIP_URL="https://github.com/$REPO/releases/download/v${VERSION}/${ZIP_NAME}"
ZIP_PATH="$TMP_DIR/$ZIP_NAME"

echo "==> Downloading $ZIP_URL"
if ! fetch_file "$ZIP_URL" "$ZIP_PATH" || [ ! -s "$ZIP_PATH" ]; then
    echo "error: download failed — is v$VERSION a published release of $REPO?" >&2
    echo "  Releases: https://github.com/$REPO/releases" >&2
    exit 1
fi

STAGE="$TMP_DIR/stage"
mkdir -p "$STAGE"

echo "==> Unpacking $ZIP_NAME"
if have unzip; then
    unzip -q "$ZIP_PATH" -d "$STAGE"
else
    # zipfile does not restore the executable bit; chmod below covers that.
    "$PY" -m zipfile -e "$ZIP_PATH" "$STAGE"
fi

if [ ! -f "$STAGE/install.sh" ] || [ ! -d "$STAGE/$NAME" ]; then
    echo "error: $ZIP_NAME does not look like a $NAME release archive." >&2
    exit 1
fi

echo "==> Installing into $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
# Drop the old package tree so modules deleted upstream do not linger, then
# copy over the rest. .venv and .env are untouched: the archive ships neither.
rm -rf "${INSTALL_DIR:?}/$NAME"
cp -R "$STAGE"/. "$INSTALL_DIR"/
chmod +x "$INSTALL_DIR"/*.sh

# `curl … | bash` leaves stdin pointing at the script stream, which the child
# scripts must not read. Hand them the terminal instead, so setup.sh's ffmpeg
# install can prompt for a sudo password, or nothing at all when there is no
# terminal.
if [ -r /dev/tty ]; then
    CHILD_STDIN=/dev/tty
else
    CHILD_STDIN=/dev/null
fi

cd "$INSTALL_DIR"
./setup.sh <"$CHILD_STDIN"
./install.sh <"$CHILD_STDIN"

case "$(basename "${SHELL:-}")" in
    zsh) RC="~/.zshrc" ;;
    bash) RC="~/.bashrc" ;;
    *) RC="your shell's rc file" ;;
esac

echo ""
echo "$NAME v$VERSION is installed in $INSTALL_DIR"

case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *)
        cat <<EOF

\`$NAME\` lives in ~/.local/bin, which is not on your PATH. Add this to $RC and
open a new terminal:
    export PATH="\$HOME/.local/bin:\$PATH"
EOF
        ;;
esac

CONFIG_ENV="${XDG_CONFIG_HOME:-$HOME/.config}/$NAME/.env"

cat <<EOF

Settings: $CONFIG_ENV
  OPENAI_API_KEY  required — $NAME asks for it the first time it is needed

Upgrade:    curl -fsSL https://raw.githubusercontent.com/$REPO/master/get.sh | bash
Uninstall:  $INSTALL_DIR/uninstall.sh && rm -rf $INSTALL_DIR
            (settings are kept; remove them with: rm -rf $(dirname "$CONFIG_ENV"))
EOF
