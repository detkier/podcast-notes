import os
import subprocess
import tempfile
from openai import OpenAI
from config import OPENAI_API_KEY

MAX_BYTES = 24 * 1024 * 1024  # 24MB，低於 API 25MB 上限


def _compress(audio_path: str) -> str:
    """壓縮成 64kbps mono mp3，大幅縮小檔案。"""
    out = audio_path.replace(".mp3", "_compressed.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ab", "64k", out],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )
    return out


def _split(audio_path: str) -> list[str]:
    """超過 24MB 就切成兩段。"""
    out1 = audio_path.replace(".mp3", "_p1.mp3")
    out2 = audio_path.replace(".mp3", "_p2.mp3")
    # 先取得總時長
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    half = duration / 2
    subprocess.run(
        ["ffmpeg", "-y", "-i", audio_path, "-t", str(half), "-c", "copy", out1],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", audio_path, "-ss", str(half), "-c", "copy", out2],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )
    return [out1, out2]


def transcribe(audio_path: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)

    # 先壓縮
    compressed = _compress(audio_path)
    size = os.path.getsize(compressed)
    print(f"  壓縮後：{size/1024/1024:.1f} MB")

    # 若仍超過則切段
    if size > MAX_BYTES:
        parts = _split(compressed)
        os.unlink(compressed)
    else:
        parts = [compressed]

    texts = []
    for i, part in enumerate(parts):
        print(f"  轉錄第 {i+1}/{len(parts)} 段...")
        with open(part, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="zh",
            )
        texts.append(result.text)
        os.unlink(part)

    return "\n".join(texts)
