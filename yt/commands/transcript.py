"""Download a video (YouTube, bilibili, etc.) and transcribe its audio to an SRT subtitle file.

The transcript is generated from the audio (via faster-whisper), independent of
any site-provided captions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from faster_whisper import WhisperModel
from tqdm import tqdm

from ..utils.cacheUtils import reset_cache_dir
from .download import download

SUPPORTED_LANGS = ("en", "zh", "ja")
DEFAULT_LANG = "en"


def prompt_language(default: str = DEFAULT_LANG) -> str:
    """Interactively pick a language code from SUPPORTED_LANGS.

    Accepts either the list number (1, 2, …) or the language code itself.
    Pressing Enter chooses ``default``. Aborts with a clear error when stdin
    is not a TTY, so scripted callers fail fast instead of hanging on input().
    """
    if not sys.stdin.isatty():
        print(
            "error: language selection requires an interactive terminal "
            f"(supported: {', '.join(SUPPORTED_LANGS)})",
            file=sys.stderr,
        )
        sys.exit(2)

    print("Select language:")
    for i, code in enumerate(SUPPORTED_LANGS, start=1):
        marker = "  (default)" if code == default else ""
        print(f"  {i}) {code}{marker}")
    while True:
        try:
            choice = input(f"Choice [default: {default}]: ").strip().lower()
        except EOFError:
            print()
            sys.exit(2)
        if not choice:
            return default
        if choice in SUPPORTED_LANGS:
            return choice
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(SUPPORTED_LANGS):
                return SUPPORTED_LANGS[idx]
        print(f"  Invalid choice: {choice!r}. Try again.")


def _format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        millis = 0
        secs += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe(
    media_path: Path,
    language: str,
    model_size: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    print(f"==> Loading whisper model '{model_size}' (first run downloads ~hundreds of MB)")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"==> Transcribing {media_path.name} (lang={language})")
    segments, info = model.transcribe(
        str(media_path),
        language=language,
        vad_filter=True,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    srt_path = output_dir / f"{media_path.stem}.srt"
    txt_path = output_dir / f"{media_path.stem}.txt"
    total = float(getattr(info, "duration", 0) or 0)
    bar = tqdm(
        total=round(total, 2) if total else None,
        unit="s",
        bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]",
    )
    last_end = 0.0
    with srt_path.open("w", encoding="utf-8") as srt, txt_path.open("w", encoding="utf-8") as txt:
        for index, seg in enumerate(segments, start=1):
            text = seg.text.strip()
            srt.write(f"{index}\n")
            srt.write(f"{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}\n")
            srt.write(f"{text}\n\n")
            txt.write(f"{text}\n")
            if total:
                bar.update(max(0.0, min(seg.end, total) - last_end))
                last_end = min(seg.end, total)
    bar.close()
    return srt_path, txt_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe an online video (YouTube, bilibili, ...) or local media file to SRT and TXT."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-u", "--url", help="Video URL (YouTube, bilibili, ...)")
    source.add_argument("-f", "--file", type=Path, help="Path to a local media file")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save .srt and .txt (default: same folder as the video file, or CWD for URLs)",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="faster-whisper model size: tiny, base, small, medium, large-v3 (default: small)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to read cookies from (e.g. chrome, firefox, safari, brave, edge)",
    )
    args = parser.parse_args(argv)

    # Validate any local input before clearing the cache, so a bad path doesn't
    # cause us to nuke the cache for nothing.
    if args.file and not args.file.is_file():
        parser.error(f"file not found: {args.file}")

    # Pick language interactively *before* clearing the cache and downloading,
    # so an aborted prompt doesn't waste work.
    language = prompt_language()

    reset_cache_dir()

    base_dir = args.output_dir or (args.file.parent if args.file else Path.cwd())
    if args.url:
        media_path = download(
            args.url,
            base_dir,
            audio_only=False,
            cookies_from_browser=args.cookies_from_browser,
        )
        output_dir = base_dir / media_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        new_media_path = output_dir / media_path.name
        media_path.rename(new_media_path)
        media_path = new_media_path
    else:
        media_path = args.file
        output_dir = base_dir
    srt_path, txt_path = transcribe(media_path, language, args.model, output_dir)
    print(f"==> Wrote {srt_path}")
    print(f"==> Wrote {txt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
