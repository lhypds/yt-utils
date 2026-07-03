"""Summarize a video (YouTube, bilibili, etc.) by transcribing it and asking OpenAI for the main points."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from ..utils.cacheUtils import reset_cache_dir
from .download import download
from .transcript import prompt_language, transcribe

DEFAULT_MODEL = "gpt-5.5"

PROMPT = (
    "You are reading the transcript of a video. Extract the most "
    "informational content — the specific facts, claims, numbers, names, "
    "events, and conclusions a viewer would actually want to take away. "
    "Skip filler, intros, sponsor reads, and rhetorical throat-clearing. "
    "Write it as natural prose, not a bulleted list. Be faithful to the "
    "transcript and do not invent details. "
    "Then summarize and list out the most important points."
)


def summarize_text(transcript: str, model: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": transcript},
        ],
    )
    return response.choices[0].message.content or ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a video (YouTube, bilibili, ...), transcribe it, and summarize the main points."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-u", "--url", help="Video URL (YouTube, bilibili, ...)")
    source.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to a local media file or an existing .txt transcript",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save .txt, .srt, and .summary.md (default: same folder as the video file, or CWD for URLs)",
    )
    parser.add_argument(
        "--whisper-model",
        default="small",
        help="faster-whisper model size: tiny, base, small, medium, large-v3 (default: small)",
    )
    parser.add_argument(
        "--openai-model",
        default=DEFAULT_MODEL,
        help=f"OpenAI chat model to use for summarization (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to read cookies from (e.g. chrome, firefox, safari, brave, edge)",
    )
    args = parser.parse_args(argv)

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        parser.error(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    # Resolve and (when needed) read inputs *before* clearing the cache, so an
    # input that happens to live inside ~/.cache/yt isn't wiped out from under
    # us when reset_cache_dir() runs.
    preloaded_transcript: str | None = None
    preloaded_stem: str | None = None
    if args.file and args.file.suffix.lower() == ".txt":
        if not args.file.is_file():
            parser.error(f"file not found: {args.file}")
        preloaded_transcript = args.file.read_text(encoding="utf-8")
        preloaded_stem = args.file.stem
    elif args.file is not None and not args.file.is_file():
        parser.error(f"file not found: {args.file}")

    # Prompt for language *before* clearing the cache so an aborted prompt
    # doesn't wipe anything. Only needed when we're going to transcribe.
    language: str | None = None
    if preloaded_transcript is None:
        language = prompt_language()

    reset_cache_dir()

    if preloaded_transcript is not None:
        output_dir = args.output_dir or (args.file.parent if args.file else Path.cwd())
        txt_path = output_dir / f"{preloaded_stem}.txt"
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(preloaded_transcript, encoding="utf-8")
    else:
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
        _, txt_path = transcribe(
            media_path, language, args.whisper_model, output_dir
        )

    transcript_text = txt_path.read_text(encoding="utf-8").strip()
    if not transcript_text:
        print(f"error: transcript at {txt_path} is empty", file=sys.stderr)
        return 1

    print(f"==> Summarizing {txt_path.name} with {args.openai_model}")
    summary = summarize_text(transcript_text, args.openai_model)

    summary_path = output_dir / f"{txt_path.stem}.summary.md"
    summary_path.write_text(summary + "\n", encoding="utf-8")
    print(f"==> Wrote {summary_path}")
    print()
    print(summary)

    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.run([opener, str(summary_path)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
