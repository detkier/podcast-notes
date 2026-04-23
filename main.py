import os
import tempfile
from datetime import datetime
from config import PODCASTS
from fetchers.rss import get_latest_episode, download_audio
from transcribe.whisper import transcribe
from notes.claude import generate_notes
from publishers.line import push_podcast_notes
from storage.db import init_db, already_processed, mark_processed


def slugify(text: str) -> str:
    import re
    return re.sub(r"[^\w\u4e00-\u9fff\-]", "_", text)[:60]


def process_podcast(name: str, feed_url: str):
    print(f"\n{'='*50}")
    print(f"處理：{name}")

    episode = get_latest_episode(feed_url)
    if not episode:
        print("  無法取得最新集數")
        return

    print(f"  集數：{episode['title']}")
    print(f"  發布：{episode['published']}")

    if already_processed(episode["audio_url"]):
        print("  已處理過，跳過")
        return

    # 下載音檔
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    print("  下載音檔中...")
    if not download_audio(episode["audio_url"], tmp_path):
        return

    size_mb = os.path.getsize(tmp_path) / 1024 / 1024
    print(f"  檔案大小：{size_mb:.1f} MB")

    # 轉錄
    print("  Whisper 轉錄中...")
    transcript = transcribe(tmp_path)
    os.unlink(tmp_path)
    print(f"  逐字稿長度：{len(transcript)} 字")

    # 生成筆記
    print("  Claude 整理筆記中...")
    notes = generate_notes(name, episode["title"], transcript)

    # 儲存
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{slugify(name)}_{slugify(episode['title'])}.md"
    out_path = os.path.join("outputs", filename)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {episode['title']}\n")
        f.write(f"**節目：** {name}  \n")
        f.write(f"**發布：** {episode['published']}  \n")
        f.write(f"**整理日期：** {date_str}  \n\n")
        f.write("---\n\n")
        f.write(notes)

    print(f"  筆記已儲存：{out_path}")

    # 推送摘要到 LINE
    print("  推送到 LINE...")
    push_podcast_notes(name, episode["title"], notes)

    mark_processed(episode["audio_url"], name, episode["title"])


def main():
    init_db()
    os.makedirs("outputs", exist_ok=True)
    for name, feed_url in PODCASTS.items():
        process_podcast(name, feed_url)


if __name__ == "__main__":
    main()
