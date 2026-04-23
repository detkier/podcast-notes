import feedparser
import requests
import os
import tempfile


def get_latest_episode(feed_url: str):
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return None
    e = feed.entries[0]
    audio_url = next(
        (enc.href for enc in e.get("enclosures", []) if "audio" in enc.get("type", "")),
        None,
    )
    if not audio_url:
        return None
    return {
        "title": e.get("title", ""),
        "published": e.get("published", ""),
        "audio_url": audio_url,
        "duration": e.get("itunes_duration", ""),
    }


def download_audio(audio_url: str, dest_path: str) -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        with requests.get(audio_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"下載失敗：{e}")
        return False
