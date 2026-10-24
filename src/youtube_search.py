"""Discover YouTube videos without downloading media during search."""
import re

from src.downloader import base_ydl_options, yt_dlp


def search_videos(query: str, limit: int = 10) -> list[dict]:
    query = query.strip()
    if not query:
        raise ValueError("Enter a YouTube search phrase.")
    if not 1 <= limit <= 10:
        raise ValueError("Search limit must be between 1 and 10.")
    options = {
        **base_ydl_options("data/videos"),
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        result = downloader.extract_info(f"ytsearch{limit}:{query}", download=False)
    videos, seen = [], set()
    for entry in (result or {}).get("entries", []):
        if not entry or not entry.get("id") or entry.get("is_live"):
            continue
        title = entry.get('title') or ''
        if re.search(r'\breviews?\b',query,re.I) and re.search(r'\b(trailer|teaser|rumou?rs?|leaks?|concept|advertisement|promo)\b',title,re.I):
            continue
        video_id = entry["id"]
        if video_id in seen:
            continue
        seen.add(video_id)
        videos.append({
            "id": video_id,
            "title": entry.get("title") or video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })
    if not videos:
        raise RuntimeError("YouTube returned no usable videos for this search.")
    return videos[:limit]
