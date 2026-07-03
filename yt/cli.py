"""yt CLI dispatcher.

Usage: yt <command> [args...]

Forwards all arguments after <command> to yt.commands.<command>'s main().
"""

from __future__ import annotations

import importlib
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path

# One-line description + sample invocations shown by `yt -h`. Keep examples
# minimal — full per-command options are reachable via `yt <command> -h`.
COMMAND_HELP: dict[str, tuple[str, tuple[str, ...]]] = {
    "download": (
        "Download a video from YouTube, bilibili, or any yt-dlp supported site.",
        ("yt download -u <URL>",),
    ),
    "transcript": (
        "Transcribe an online video or local media file (prompts for language).",
        (
            "yt transcript -u <URL>",
            "yt transcript -f <FILE>",
        ),
    ),
    "summarize": (
        "Summarize a video using OpenAI (prompts for language unless input is .txt).",
        (
            "yt summarize -u <URL>",
            "yt summarize -f <FILE>",
            "yt summarize -f <FILE.txt>",
        ),
    ),
    "update": (
        "Update yt to the latest release on GitHub (lhypds/yt).",
        (
            "yt update",
            "yt update -f",
        ),
    ),
}


def _version_string() -> str:
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
        entry = COMMAND_HELP.get(cmd)
        if entry is None:
            print(f"  {cmd}")
            continue
        description, examples = entry
        print(f"  {cmd:<{name_width}}  {description}")
        for example in examples:
            print(f"  {' ' * name_width}    {example}")
    print()
    print("Run `yt <command> -h` for the full options of a single command.")


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-v", "--version"):
        print(_version_string())
        return 0

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
