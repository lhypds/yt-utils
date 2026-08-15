"""Update yt to the latest GitHub release.

`get.sh` on master is the same installer the README tells users to curl, and it
already knows how to download a release, unpack it over an existing install
(keeping `.venv` and `.env`), and re-run `setup.sh` / `install.sh`. So this
command only decides *whether* to update — the work itself is handed to that
script, which keeps installing and updating from drifting apart.

Usage:
    yt update              # update when a newer release exists
    yt update -f|--force   # re-run the installer even when up to date
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from ..cli import version_string

REPO = "lhypds/yt"
BRANCH = "master"

GET_SH_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/get.sh"
LATEST_RELEASE_URL = f"https://github.com/{REPO}/releases/latest"
LATEST_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

LAUNCHER = Path.home() / ".local" / "bin" / "yt"
LAUNCHER_MARKER = "# yt-launcher:REPO="
# Kept in step with get.sh, which is what actually does the installing.
_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
DEFAULT_INSTALL_DIR = _DATA_HOME / "yt"
LEGACY_INSTALL_DIR = Path.home() / ".yt"  # where earlier releases unpacked to

USER_AGENT = "yt-updater"


# ── github ──────────────────────────────────────────────────────────────────

def _open(url: str, *, method: str = "GET", timeout: int = 15):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT}, method=method
    )
    return urllib.request.urlopen(request, timeout=timeout)


def latest_version() -> str:
    """The newest published release version, or "" when it cannot be read."""
    # /releases/latest redirects to the newest tag, which costs no API quota.
    try:
        with _open(LATEST_RELEASE_URL, method="HEAD") as response:
            tag = response.url.rstrip("/").rsplit("/", 1)[-1]
        if tag.startswith("v") and tag[1:2].isdigit():
            return tag[1:]
    except OSError:
        pass
    try:
        with _open(LATEST_API_URL) as response:
            tag = json.loads(response.read().decode()).get("tag_name", "")
    except (OSError, ValueError):
        return ""
    return str(tag).lstrip("v")


# ── versions ────────────────────────────────────────────────────────────────

def _numbers(version: str) -> tuple[int, ...] | None:
    parts = version.lstrip("v").split(".")
    if not parts or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def is_newer(latest: str, current: str) -> bool:
    latest_numbers, current_numbers = _numbers(latest), _numbers(current)
    if latest_numbers is None or current_numbers is None:
        # Unparseable on either side: treat any difference as an update.
        return latest.lstrip("v") != current.lstrip("v")
    return latest_numbers > current_numbers


# ── install location ────────────────────────────────────────────────────────

def _launcher_target() -> Path | None:
    """The install root recorded in the launcher install.sh wrote."""
    try:
        lines = LAUNCHER.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        if line.startswith(LAUNCHER_MARKER):
            path = line[len(LAUNCHER_MARKER):].strip()
            if path:
                return Path(path)
    return None


def _same_path(a: Path, b: Path) -> bool:
    """Whether two paths name the same place once symlinks are resolved.

    One side of the comparison below comes from ``__file__.resolve()`` and the
    other is built from ``Path.home()``, so ``==`` alone would miss the match
    wherever the home directory is reached through a symlink — which is the
    normal arrangement on Fedora Silverblue (``/home`` → ``/var/home``) and on
    macOS for anything under ``/tmp``.
    """
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return a == b


def install_dir() -> Path:
    """The install to overwrite: the one this code runs from, when that is a
    release tree; else whatever the launcher points at; else get.sh's default."""
    root = Path(__file__).resolve().parents[2]
    if (root / "install.sh").is_file() and (root / "VERSION").is_file():
        target = root
    else:
        target = _launcher_target() or DEFAULT_INSTALL_DIR
    # An install still sitting at the pre-XDG ~/.yt is named as the new default
    # rather than as itself, so that get.sh moves it there instead of upgrading
    # it in place for ever. Passing it back its own path would suppress the very
    # migration it needs, since get.sh only migrates when installing to the
    # default location.
    if _same_path(target, LEGACY_INSTALL_DIR):
        return DEFAULT_INSTALL_DIR
    return target


# ── installer ───────────────────────────────────────────────────────────────

def run_installer(version: str, target: Path) -> int:
    print(f"==> Fetching the installer from {GET_SH_URL}")
    try:
        with _open(GET_SH_URL, timeout=30) as response:
            script = response.read()
    except OSError as e:
        print(f"error: could not download get.sh: {e}", file=sys.stderr)
        print(f"  Update by hand with:  curl -fsSL {GET_SH_URL} | bash", file=sys.stderr)
        return 1
    if not script.startswith(b"#!"):
        print("error: the downloaded get.sh is not a shell script.", file=sys.stderr)
        return 1

    # get.sh replaces the package tree this module was imported from, so run it
    # from a temporary directory outside the install — and import nothing after.
    with tempfile.TemporaryDirectory(prefix="yt-update-") as tmp:
        script_path = Path(tmp) / "get.sh"
        script_path.write_bytes(script)
        sys.stdout.flush()  # keep our lines ahead of the installer's when piped
        return subprocess.run(
            ["bash", str(script_path), "--version", version, "--dir", str(target)]
        ).returncode


# ── entry point ─────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yt update",
        description="Update yt to the latest GitHub release.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Re-run the installer even when already up to date",
    )
    args = parser.parse_args(argv)

    current = version_string()
    print(f"Current version : v{current}")

    print("Checking for updates ...")
    latest = latest_version()
    if not latest:
        print(f"error: could not determine the latest release of {REPO}.", file=sys.stderr)
        print(f"  Releases: https://github.com/{REPO}/releases", file=sys.stderr)
        return 1
    print(f"Latest version  : v{latest}")

    if is_newer(latest, current):
        print(f"Update available: v{current} → v{latest}")
    elif args.force:
        print("Already up to date — reinstalling because --force was given.")
    else:
        print("Already up to date.")
        return 0

    target = install_dir()
    if (target / ".git").exists():
        print(f"error: {target} is a git checkout, which get.sh will not overwrite.", file=sys.stderr)
        print(f"  Update it with:  git -C {target} pull && ./setup.sh && ./install.sh", file=sys.stderr)
        return 1
    print(f"Updating        : {target}")

    code = run_installer(latest, target)
    if code != 0:
        print(f"error: the installer exited with code {code}.", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
