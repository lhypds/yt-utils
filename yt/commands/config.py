"""Open yt's settings file in an editor.

Settings live in ``~/.config/yt/.env`` (see ``yt.utils.configUtils`` for the
full precedence rules). This command is just an editor in front of that file:
it creates the file from the shipped template when it is missing, opens
``$VISUAL`` / ``$EDITOR``, and afterwards reports which keys ended up set —
never their values, which are secrets and have no business in a scrollback.

Usage:
    yt config           # edit the settings file
    yt config --path    # print its path (for scripts: "$(yt config --path)")
    yt config --show    # list which keys are set, without opening an editor
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

from ..utils.configUtils import KEY_SOURCES, config_path

# Used only when the install is missing its .env.example (it ships in every
# release archive, so this is a belt-and-braces fallback).
TEMPLATE = """\
# Used by `yt summarize`.
OPENAI_API_KEY=
"""

# Why each key matters, shown by --show and after an edit.
KEY_PURPOSE: dict[str, str] = {
    "OPENAI_API_KEY": "required for `yt summarize`",
}

# Tried in order when neither $VISUAL nor $EDITOR is set. nano first: it is the
# one an unprepared user can actually exit.
FALLBACK_EDITORS = ("nano", "vim", "vi")


def _ensure_file(path: Path) -> bool:
    """Create the settings file from the template. True when it was created."""
    if path.is_file():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    example = Path(__file__).resolve().parents[2] / ".env.example"
    text = example.read_text(encoding="utf-8") if example.is_file() else TEMPLATE
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)  # it holds secrets
    return True


def _editor() -> list[str] | None:
    """The editor command to run, or ``None`` when there is nothing to run.

    ``$EDITOR`` may carry flags (``code -w``, ``emacsclient -nw``), so it is
    split as a shell word list rather than treated as a bare program name.
    """
    for variable in ("VISUAL", "EDITOR"):
        value = (os.environ.get(variable) or "").strip()
        if value:
            try:
                parts = shlex.split(value)
            except ValueError:  # unbalanced quotes — take it literally
                parts = [value]
            if parts:
                return parts
    for candidate in FALLBACK_EDITORS:
        if shutil.which(candidate):
            return [candidate]
    return None


def _report(path: Path) -> None:
    """Print which keys are set in ``path``, without revealing any value."""
    # dotenv_values reads the file directly, so this reflects what was just
    # saved — unlike configUtils.get_key, which caches and lets an exported
    # shell variable mask what the file actually contains.
    values = {name: (value or "").strip() for name, value in dotenv_values(path).items()}

    print(f"Settings: {path}")
    for name, purpose in KEY_PURPOSE.items():
        if values.get(name):
            print(f"  {name} is set")
        else:
            print(f"  {name} is not set — {purpose}")
            print(f"      get a key: {KEY_SOURCES[name]}")

    exported = [name for name in KEY_PURPOSE if (os.environ.get(name) or "").strip()]
    if exported:
        # The real environment outranks the file, so an exported key silently
        # wins over whatever was just edited here.
        print(
            f"  note: {', '.join(exported)} also exported in your shell, which takes precedence"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yt config",
        description="Open yt's settings file (API keys) in your editor.",
    )
    parser.add_argument(
        "--path", action="store_true", help="Print the settings file path and exit"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="List which keys are set (no values) instead of opening an editor",
    )
    args = parser.parse_args(argv)

    path = config_path()

    if args.path:
        print(path)
        return 0

    created = _ensure_file(path)
    if created:
        print(f"==> Created {path}", file=sys.stderr)

    if args.show:
        _report(path)
        return 0

    editor = _editor()
    if editor is None:
        print("error: no editor found — set $EDITOR or $VISUAL.", file=sys.stderr)
        print(f"  Edit this file by hand instead: {path}", file=sys.stderr)
        return 1

    try:
        completed = subprocess.run([*editor, str(path)])
    except OSError as err:
        print(f"error: could not run {editor[0]}: {err}", file=sys.stderr)
        print(f"  Edit this file by hand instead: {path}", file=sys.stderr)
        return 1

    if completed.returncode != 0:
        print(
            f"warning: {editor[0]} exited with status {completed.returncode}",
            file=sys.stderr,
        )

    # Editors that save by writing a new file and renaming it over the old one
    # give the replacement default permissions, dropping the 0600 set above.
    path.chmod(0o600)
    _report(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
