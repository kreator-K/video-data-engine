"""Search YouTube and process the first ten results through the existing pipeline."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.youtube_search import search_videos


def run_search(query: str, output_dir: Path | None = None, progress=None, reference_urls=None) -> dict:
    from dotenv import load_dotenv
    load_dotenv()
    if os.getenv("VISION_PROVIDER", "anthropic").lower() == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set ANTHROPIC_API_KEY before starting a search analysis.")
    def update(message):
        print(message, flush=True)
        if progress:
            progress(message)

    update(f"Searching YouTube for: {query}")
    if reference_urls:
        from src.presentation import video_key
        references = [{'id': video_key(url), 'url': url, 'title': 'Reference video'} for url in reference_urls]
        discovered = search_videos(query, limit=10) if len(references) < 10 else []
        videos, seen = [], set()
        for video in references + discovered:
            if video['id'] not in seen:
                seen.add(video['id'])
                videos.append(video)
        videos = videos[:10]
    else:
        videos = search_videos(query, limit=10)
    update(f"Found {len(videos)}/10 videos. Processing in YouTube search order.")
    if len(videos) < 10:
        update("YouTube returned fewer than ten usable results; processing those available.")
    output_dir = output_dir or Path("data/search_runs") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"query": query, "requested": 10, "sources": videos, "results": []}
    path = output_dir / "summary.json"

    def save():
        path.write_text(json.dumps(manifest, indent=2) + "\n")

    save()
    from main import run_pipeline

    for index, video in enumerate(videos, 1):
        update(f"Video {index}/{len(videos)}: {video['title']}")
        try:
            report_path = run_pipeline(video["url"])
            row = {**video, "status": "completed", "report_path": str(report_path)}
        except Exception as exc:
            row = {**video, "status": "failed", "error": str(exc)}
            update(f"Video {index} failed: {exc}")
        manifest["results"].append(row)
        save()
    completed = sum(row["status"] == "completed" for row in manifest["results"])
    update(f"Finished: {completed}/{len(videos)} completed. Summary: {path}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="YouTube search phrase")
    args = parser.parse_args()
    result = run_search(args.query or input("YouTube search phrase: "))
    raise SystemExit(0 if all(r["status"] == "completed" for r in result["results"]) else 1)
