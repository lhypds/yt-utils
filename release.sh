#!/usr/bin/env bash
# Build a source-tree release zip and hand off to release_gh.sh to publish on
# GitHub (lhypds/yt). The archive contains everything `install.sh` needs to set
# up a fresh checkout: the `yt/` package, top-level scripts, requirements, etc.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

normalize_version() {
    local v="$1"
    v="${v#v}"
    v="$(printf '%s' "$v" | tr -d '[:space:]')"
    printf '%s' "$v"
}

version_compare() {
    local lhs="$1"
    local rhs="$2"
    local IFS='.'
    local -a a_parts b_parts
    local max_len i a_seg b_seg

    read -r -a a_parts <<< "$lhs"
    read -r -a b_parts <<< "$rhs"

    max_len="${#a_parts[@]}"
    if [ "${#b_parts[@]}" -gt "$max_len" ]; then
        max_len="${#b_parts[@]}"
    fi

    for ((i = 0; i < max_len; i++)); do
        a_seg="${a_parts[i]:-0}"
        b_seg="${b_parts[i]:-0}"
        if ! [[ "$a_seg" =~ ^[0-9]+$ ]] || ! [[ "$b_seg" =~ ^[0-9]+$ ]]; then
            echo "Error: VERSION contains non-numeric segments ($lhs vs $rhs)."
            exit 1
        fi

        if ((10#$a_seg > 10#$b_seg)); then
            echo 1
            return
        fi
        if ((10#$a_seg < 10#$b_seg)); then
            echo -1
            return
        fi
    done

    echo 0
}

bump_version_interactive() {
    local current="$1"
    local IFS='.'
    local -a parts
    local count choice idx i

    read -r -a parts <<< "$current"
    count="${#parts[@]}"
    if [ "$count" -eq 0 ]; then
        echo "Error: invalid VERSION '$current'."
        exit 1
    fi

    for i in "${parts[@]}"; do
        if ! [[ "$i" =~ ^[0-9]+$ ]]; then
            echo "Error: VERSION contains non-numeric segments ($current)."
            exit 1
        fi
    done

    read -r -p "VERSION $current equals latest release. Which segment to bump from right? [1=last, 2=second last, ...] (default: 1): " choice
    choice="${choice:-1}"
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "$count" ]; then
        echo "Error: invalid segment selection '$choice'."
        exit 1
    fi

    idx=$((count - choice))
    parts[idx]=$((10#${parts[idx]} + 1))
    for ((i = idx + 1; i < count; i++)); do
        parts[i]=0
    done

    local result="${parts[0]}"
    for ((i = 1; i < count; i++)); do
        result+=".${parts[i]}"
    done
    printf '%s' "$result"
}

prepare_version_for_release() {
    if [ ! -f "$ROOT_DIR/VERSION" ]; then
        echo "Error: VERSION file not found."
        exit 1
    fi

    if ! command -v gh &>/dev/null; then
        echo "Error: GitHub CLI (gh) is required."
        exit 1
    fi
    if ! gh auth status &>/dev/null; then
        echo "Error: gh is not authenticated. Run: gh auth login"
        exit 1
    fi

    local current draft_tag draft_tags latest_tag latest cmp new_version branch
    current="$(normalize_version "$(cat "$ROOT_DIR/VERSION")")"
    if [ -z "$current" ]; then
        echo "Error: VERSION file is empty."
        exit 1
    fi

    if ! draft_tags="$(gh release list --limit 1000 --json tagName,isDraft \
        --jq '.[] | select(.isDraft) | .tagName' 2>/dev/null)"; then
        echo "Error: unable to check GitHub for draft releases."
        exit 1
    fi
    if [ -n "$draft_tags" ]; then
        echo "Warning: GitHub draft release(s) found:"
        while IFS= read -r draft_tag; do
            echo "  - $draft_tag"
        done <<< "$draft_tags"
        echo "Review, publish, or delete the draft release(s) before continuing."
        exit 1
    fi

    latest_tag="$(gh release view --json tagName --jq '.tagName' 2>/dev/null || true)"
    if [ "$latest_tag" = "null" ]; then
        latest_tag=""
    fi

    if [ -z "$latest_tag" ]; then
        echo "No existing GitHub release found. Releasing VERSION $current."
        return
    fi

    latest="$(normalize_version "$latest_tag")"
    cmp="$(version_compare "$current" "$latest")"

    if [ "$cmp" -gt 0 ]; then
        echo "VERSION $current is greater than latest release $latest. Continue releasing."
        return
    fi

    if [ "$cmp" -lt 0 ]; then
        echo "Error: VERSION $current is lower than latest release $latest."
        exit 1
    fi

    new_version="$(bump_version_interactive "$current")"
    printf '%s\n' "$new_version" > "$ROOT_DIR/VERSION"

    git add "$ROOT_DIR/VERSION"
    git commit -m "$new_version"

    branch="$(git branch --show-current 2>/dev/null || true)"
    if [ -n "$branch" ]; then
        git push origin "$branch"
    else
        git push
    fi

    echo "VERSION bumped to $new_version, committed, and pushed."
}

prepare_version_for_release

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
# .python-version is deliberately NOT shipped: it is this machine's pyenv pin, and
# unpacked into the install directory it makes pyenv resolve every python there to
# that one version — breaking setup.sh on any machine that has a different one.
[ -f "$ROOT_DIR/.env.example"    ] && cp "$ROOT_DIR/.env.example"    "$STAGING_DIR/"
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
