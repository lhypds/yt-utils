"""yt CLI dispatcher.

Usage: yt <command> [args...]

Forwards all arguments after <command> to yt.commands.<command>'s main().
"""

from __future__ import annotations

import importlib
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path

# Single-letter command aliases: `yt -du <URL>` == `yt download -u <URL>`.
SHORTHANDS: dict[str, str] = {
    "d": "download",
    "s": "summarize",
    "t": "transcript",
}

# Single-letter aliases that expand straight to a command with no flag
# letter attached: `yt -c` == `yt config`.
DIRECT_SHORTHANDS: dict[str, str] = {
    "c": "config",
}

# One-line description per command shown by `yt -h`. Full per-command
# options are reachable via `yt <command> -h`.
COMMAND_HELP: dict[str, str] = {
    "download": "Download a video (-u <URL>) from any yt-dlp supported site.",
    "transcript": "Transcribe an online video (-u <URL>) or local file (-f <FILE>).",
    "summarize": "Summarize a video (-u <URL>) or file (-f <FILE>) using OpenAI.",
    "config": "Edit the settings file holding your API key (--path, --show).",
    "update": "Update yt to the latest GitHub release (-f to force).",
}


def version_string() -> str:
    root = Path(__file__).resolve().parent.parent
    vf = root / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip()
    try:
        return pkg_version("yt")
    except PackageNotFoundError:
        return "0.0.0"


def _print_help() -> None:
    available = sorted(
        p.stem
        for p in (Path(__file__).resolve().parent / "commands").glob("*.py")
        if not p.stem.startswith("_")
    )
    print("usage: yt <command> [args...]")
    print("       yt -h | --help        Show this help.")
    print("       yt -v | --version     Show the installed version.")
    print()
    print("commands:")
    name_width = max((len(c) for c in available), default=0)
    for cmd in available:
        description = COMMAND_HELP.get(cmd)
        if description is None:
            print(f"  {cmd}")
        else:
            print(f"  {cmd:<{name_width}}  {description}")
    print()
    print("shortcuts: yt -du == yt download -u  (also -su, -sf, -tu, -tf, -c)")
    print()
    print("Run `yt <command> -h` for the full options of a single command.")


def _expand_shorthand(argv: list[str]) -> list[str]:
    """Expand `-du <URL>` / `-c` style shortcuts into their full form."""
    if not argv:
        return argv
    first = argv[0]
    if len(first) < 2 or first[0] != "-" or not first[1:].isalpha():
        return argv
    letters = first[1:]
    if len(letters) == 1 and letters in DIRECT_SHORTHANDS:
        return [DIRECT_SHORTHANDS[letters], *argv[1:]]
    if len(letters) >= 2 and letters[0] in SHORTHANDS:
        return [SHORTHANDS[letters[0]], f"-{letters[1:]}", *argv[1:]]
    return argv


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-v", "--version"):
        print(version_string())
        return 0

    argv = _expand_shorthand(argv)

    if len(argv) < 1 or argv[0] in ("-h", "--help"):
        _print_help()
        return 0 if argv else 1

    command, *rest = argv
    try:
        module = importlib.import_module(f"yt.commands.{command}")
    except ModuleNotFoundError:
        print(f"yt: unknown command '{command}'", file=sys.stderr)
        return 2

    return module.main(rest)


def run() -> int:
    """Console script entry point (reads sys.argv)."""
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
