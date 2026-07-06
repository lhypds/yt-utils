"""Custom yt-dlp extractor for Threads (threads.com / threads.net)."""

from __future__ import annotations

import json
import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError


class ThreadsIE(InfoExtractor):
    """Extractor for Threads (threads.com / threads.net) video posts.

    yt-dlp has no built-in Threads extractor. Threads only server-renders
    post data (including direct video URLs) for known crawlers, so fetch
    the page with a Googlebot user agent and pull the post JSON out of the
    embedded ``application/json`` script tags.
    """

    IE_NAME = "Threads"
    _VALID_URL = (
        r"https?://(?:www\.)?threads\.(?:com|net)/"
        r"(?:@[^/]+/)?(?:post|t)/(?P<id>[A-Za-z0-9_-]+)"
    )
    _CRAWLER_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

    def _find_post(self, obj, code):
        # The page embeds the whole thread (post + replies); locate the
        # media object whose short code matches the URL.
        if isinstance(obj, dict):
            if obj.get("code") == code and (
                obj.get("video_versions") or obj.get("carousel_media")
            ):
                return obj
            values = obj.values()
        elif isinstance(obj, list):
            values = obj
        else:
            return None
        for value in values:
            found = self._find_post(value, code)
            if found:
                return found
        return None

    def _real_extract(self, url):
        post_code = self._match_id(url)
        webpage = self._download_webpage(
            url, post_code, headers={"User-Agent": self._CRAWLER_UA}
        )

        post = None
        for mobj in re.finditer(
            r'<script type="application/json"[^>]*>(.*?)</script>', webpage, re.DOTALL
        ):
            blob = mobj.group(1)
            if post_code not in blob:
                continue
            try:
                data = json.loads(blob)
            except ValueError:
                continue
            post = self._find_post(data, post_code)
            if post:
                break
        if post is None:
            raise ExtractorError(
                "Could not find Threads post data (deleted or restricted post?)",
                expected=True,
            )

        if not post.get("video_versions"):
            post = next(
                (
                    item
                    for item in post.get("carousel_media") or []
                    if item.get("video_versions")
                ),
                post,
            )
        video_versions = post.get("video_versions") or []
        if not video_versions:
            raise ExtractorError("Threads post contains no video", expected=True)

        # Versions are ordered best-first; type is an opaque quality tag
        # (101/102/103) and the URLs are frequently identical.
        seen_urls = set()
        formats = []
        for version in video_versions:
            video_url = version.get("url")
            if not video_url or video_url in seen_urls:
                continue
            seen_urls.add(video_url)
            formats.append(
                {
                    "url": video_url,
                    "format_id": str(version.get("type", len(formats))),
                    "ext": "mp4",
                    "width": post.get("original_width"),
                    "height": post.get("original_height"),
                    "quality": -len(formats),
                }
            )

        user = post.get("user") or {}
        caption = (post.get("caption") or {}).get("text") or ""
        title = caption.strip().split("\n")[0] or f"Threads post {post_code}"
        thumbnails = [
            {"url": c["url"], "width": c.get("width"), "height": c.get("height")}
            for c in (post.get("image_versions2") or {}).get("candidates", [])
            if c.get("url")
        ]

        return {
            "id": post_code,
            "title": title,
            "formats": formats,
            "uploader": user.get("username"),
            "uploader_id": str(user.get("pk") or "") or None,
            "timestamp": post.get("taken_at"),
            "thumbnails": thumbnails,
        }
