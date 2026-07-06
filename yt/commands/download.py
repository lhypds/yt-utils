"""Download a video (YouTube, bilibili, etc.) given its URL."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from yt_dlp import YoutubeDL

from ..utils.threadsUtils import ThreadsIE


def _patch_bilibili_playurl_fallback() -> None:
    """Work around HTTP 412 from bilibili's wbi-signed playurl API.

    For anonymous clients (especially outside mainland China) bilibili's risk
    control rejects ``/x/player/wbi/playurl`` with 412 Precondition Failed,
    while the legacy ``/x/player/playurl`` endpoint accepts the very same
    parameters. Retry there when the wbi call is blocked.
    """
    try:
        from yt_dlp.extractor.bilibili import BilibiliBaseIE
        from yt_dlp.networking.exceptions import HTTPError
        from yt_dlp.utils import ExtractorError
    except ImportError:
        return
    if getattr(BilibiliBaseIE, "_yt_playurl_fallback", False):
        return

    original = BilibiliBaseIE._download_playinfo

    def _download_playinfo(self, bvid, cid, *args, **kwargs):
        try:
            return original(self, bvid, cid, *args, **kwargs)
        except ExtractorError as err:
            if not (isinstance(err.cause, HTTPError) and err.cause.status == 412):
                raise
            self.to_screen(
                "wbi playurl API blocked (HTTP 412); retrying via legacy endpoint"
            )
            params = {"bvid": bvid, "cid": cid, "fnval": 4048}
            extra_query = kwargs.get("query")
            if isinstance(extra_query, dict):
                params.update(extra_query)
            params.pop("try_look", None)
            return self._download_json(
                "https://api.bilibili.com/x/player/playurl",
                bvid,
                query=params,
                headers=kwargs.get("headers"),
                note=f"Downloading video formats for cid {cid} (legacy API)",
            )["data"]

    BilibiliBaseIE._download_playinfo = _download_playinfo
    BilibiliBaseIE._yt_playurl_fallback = True


def download(
    url: str,
    output_dir: Path,
    audio_only: bool = False,
    cookies_from_browser: str | None = None,
) -> Path:
    _patch_bilibili_playurl_fallback()
    output_dir.mkdir(parents=True, exist_ok=True)

    # `channel` is YouTube-specific; other sites (e.g. bilibili) expose the
    # account name as `uploader` instead.
    name_template = "[%(channel,uploader|NA)s]_[%(title)s].%(ext)s"
    opts: dict = {
        "outtmpl": str(output_dir / name_template),
        "noplaylist": True,
        # The Python API defaults to 0 retries (unlike the CLI's 10), which
        # makes flaky CDN mirrors (e.g. bilibili's overseas ones) fatal.
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "extractor_args": {
            "youtube": {"player_client": ["tv_simply", "mweb", "default"]}
        },
    }
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)

    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        opts["format"] = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
            "/bestvideo+bestaudio"
            "/best[ext=mp4]/best"
        )
        opts["merge_output_format"] = "mp4"

    with YoutubeDL(opts) as ydl:
        # ThreadsIE is not in yt-dlp's registry, so register it on this
        # instance and route matching URLs to it explicitly (extractors
        # added here would otherwise be shadowed by the generic one).
        ie_key = None
        if re.match(ThreadsIE._VALID_URL, url):
            ydl.add_info_extractor(ThreadsIE())
            ie_key = "Threads"
        info = ydl.extract_info(url, download=True, ie_key=ie_key)
        downloads = info.get("requested_downloads") or []
        if downloads and downloads[-1].get("filepath"):
            return Path(downloads[-1]["filepath"])
        return Path(ydl.prepare_filename(info))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a video from YouTube, bilibili, or any yt-dlp supported site."
    )
    parser.add_argument("-u", "--url", required=True, help="Video URL (YouTube, bilibili, ...)")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to save the video into (default: current directory)",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only (mp3) instead of video",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to read cookies from (e.g. chrome, firefox, safari, brave, edge)",
    )
    args = parser.parse_args(argv)

    download(
        args.url,
        args.output_dir,
        audio_only=args.audio_only,
        cookies_from_browser=args.cookies_from_browser,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
