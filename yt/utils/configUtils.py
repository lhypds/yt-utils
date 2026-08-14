"""Where ``yt`` keeps its settings, and how it asks for a missing API key.

Settings live in ``~/.config/yt/.env`` (``$XDG_CONFIG_HOME/yt/.env`` when that
variable is set), so an installed ``yt`` finds its keys no matter which
directory it is run from — the old bare ``load_dotenv()`` only searched
upwards from the current working directory, which never found anything once
``yt`` was installed outside a checkout.

Precedence, highest first:

1. the real environment — ``export OPENAI_API_KEY=…`` always wins
2. a ``.env`` beside a development checkout, so hacking on the repo needs no
   edits to ``~/.config``
3. ``~/.config/yt/.env``, written by ``setup.sh`` and by the prompt below
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

APP = "yt"

# Where to get each key, shown when one is missing.
KEY_SOURCES: dict[str, str] = {
    "OPENAI_API_KEY": "https://platform.openai.com/api-keys",
}

_loaded = False


class MissingKey(RuntimeError):
    """A required key is not set and could not be asked for interactively.

    The message is the full set-it-up instructions, ready to print.
    """


def config_dir() -> Path:
    """The directory holding ``yt``'s settings."""
    base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(base) / APP


def config_path() -> Path:
    """The settings file itself."""
    return config_dir() / ".env"


def repo_env_path() -> Path:
    """The ``.env`` of a development checkout (``<repo>/.env``)."""
    return Path(__file__).resolve().parents[2] / ".env"


def load_config() -> None:
    """Load settings into ``os.environ``. Safe to call more than once."""
    global _loaded
    if _loaded:
        return
    # load_dotenv never overwrites variables that are already set, so this
    # order gives: real environment > checkout .env > ~/.config/yt/.env.
    repo_env = repo_env_path()
    if repo_env.is_file():
        load_dotenv(repo_env)
    load_dotenv(config_path())
    _loaded = True


def get_key(name: str) -> str:
    """Return key ``name`` from the environment or settings file, or ``""``."""
    load_config()
    return (os.getenv(name) or "").strip()


def save_key(name: str, value: str) -> Path:
    """Write ``name=value`` into the settings file and the running process.

    Replaces an existing assignment (including a commented-out one) rather
    than appending a second, shadowed line.
    """
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    assignment = f"{name}={value}"
    for i, line in enumerate(lines):
        stripped = line.lstrip("# ").strip()
        if stripped.startswith(f"{name}="):
            lines[i] = assignment
            break
    else:
        lines.append(assignment)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o600)  # it holds secrets
    os.environ[name] = value
    return path


def instructions(name: str, purpose: str, note: str = "") -> str:
    """The 'here is how to set it' message for a missing key."""
    source = KEY_SOURCES.get(name)
    lines = [f"{name} is not set — {APP} needs it for {purpose}."]
    if note:
        lines.append(f"  {note}")
    if source:
        lines.append(f"  Get a key: {source}")
    lines += [
        f"  Then add it to {config_path()}:",
        f"      {name}=...",
        "  or export it in your shell:",
        f"      export {name}=...",
    ]
    return "\n".join(lines)


def _ask_for_key(name: str, purpose: str, note: str) -> str:
    """Prompt for ``name`` on the terminal. Returns ``""`` if that's not possible.

    Reads from ``/dev/tty`` rather than stdin, so prompting still works when
    ``yt`` is part of a pipeline — and so a piped stdin is never eaten.
    """
    try:
        tty = open("/dev/tty", "r")
    except OSError:
        return ""  # cron, CI, no terminal — the caller prints instructions
    tty.close()

    source = KEY_SOURCES.get(name)
    print(f"\n{name} is not set — {APP} needs it for {purpose}.", file=sys.stderr)
    if note:
        print(f"  {note}", file=sys.stderr)
    if source:
        print(f"  Get a key: {source}", file=sys.stderr)
    print(f"  It will be saved to {config_path()}.", file=sys.stderr)
    print("  Press Enter alone to cancel.", file=sys.stderr)
    try:
        # getpass reads from /dev/tty (which we just proved is open), so the
        # key never lands in the scrollback.
        return getpass.getpass(f"{name} (input hidden): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("", file=sys.stderr)
        return ""


def require_key(name: str, *, purpose: str, note: str = "") -> str:
    """Return key ``name``, asking for it once and saving it when it's missing.

    A key already present in the environment (or in a settings file) is used
    as-is, with no prompt. Raises ``MissingKey`` when there is no terminal to
    ask on, or the prompt is cancelled.
    """
    value = get_key(name)
    if value:
        return value

    value = _ask_for_key(name, purpose, note)
    if not value:
        raise MissingKey(instructions(name, purpose, note))

    path = save_key(name, value)
    print(f"==> Saved {name} to {path}\n", file=sys.stderr)
    return value
