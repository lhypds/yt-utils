#!/usr/bin/env bash
# Build a source-tree release zip and hand off to release_gh.sh to publish on
# GitHub (lhypds/yt). The archive contains everything `install.sh` needs to set
# up a fresh checkout: the `yt/` package, top-level scripts, requirements, etc.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE_DIR="$ROOT_DIR/release"
STAGING_DIR="$RELEASE_DIR/staging"

# Clear previous release artifacts
rm -rf "$RELEASE_DIR"
mkdir -p "$STAGING_DIR"
echo "Cleared previous release artifacts."

echo "==> Staging release files in $STAGING_DIR"

# Package source
cp -R "$ROOT_DIR/yt" "$STAGING_DIR/yt"

# Top-level scripts and project files
cp "$ROOT_DIR/yt.py"            "$STAGING_DIR/"
cp "$ROOT_DIR/install.sh"       "$STAGING_DIR/"
cp "$ROOT_DIR/get.sh"           "$STAGING_DIR/"
cp "$ROOT_DIR/setup.sh"         "$STAGING_DIR/"
cp "$ROOT_DIR/uninstall.sh"     "$STAGING_DIR/"
cp "$ROOT_DIR/build.sh"         "$STAGING_DIR/"
cp "$ROOT_DIR/clear.sh"         "$STAGING_DIR/"
cp "$ROOT_DIR/requirements.txt" "$STAGING_DIR/"
cp "$ROOT_DIR/pyproject.toml"   "$STAGING_DIR/"
cp "$ROOT_DIR/README.md"        "$STAGING_DIR/"
cp "$ROOT_DIR/LICENSE"          "$STAGING_DIR/"
cp "$ROOT_DIR/VERSION"          "$STAGING_DIR/"

# Optional dotfiles we want to ship if present (never .env — that has secrets).
[ -f "$ROOT_DIR/.env.example"    ] && cp "$ROOT_DIR/.env.example"    "$STAGING_DIR/"
[ -f "$ROOT_DIR/.python-version" ] && cp "$ROOT_DIR/.python-version" "$STAGING_DIR/"
[ -f "$ROOT_DIR/.gitignore"      ] && cp "$ROOT_DIR/.gitignore"      "$STAGING_DIR/"

# Strip __pycache__ from the copied package tree
find "$STAGING_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

chmod +x "$STAGING_DIR"/*.sh

VERSION="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
if [ -z "$VERSION" ]; then
    echo "Error: VERSION file is empty."
    exit 1
fi

ZIP_NAME="yt_v${VERSION}.zip"
ZIP_PATH="$RELEASE_DIR/$ZIP_NAME"

[ -f "$ZIP_PATH" ] && rm -f "$ZIP_PATH"

echo "==> Creating $ZIP_NAME"
(cd "$STAGING_DIR" && zip -r -9 "$ZIP_PATH" .) >/dev/null
echo "Created archive: $ZIP_PATH"

echo ""
echo "Release artifacts ready in $RELEASE_DIR"
echo ""

"$ROOT_DIR/release_gh.sh" "v${VERSION}" "$ZIP_PATH"
