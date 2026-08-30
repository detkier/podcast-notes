import os
import subprocess
import tempfile
from openai import OpenAI
from config import OPENAI_API_KEY

MAX_BYTES = 24 * 1024 * 1024  # 24MB，低於 API 25MB 上限

# 台股投資詞彙庫：提示 Whisper 優先辨識這些專有名詞
WHISPER_PROMPT = """
台股投資Podcast。常見詞彙：
股票、大盤、加權指數、櫃買、成交量、漲停、跌停、處置股票、除息、除權、融資、融券、主力、法人、外資、投信、自營商、
矽晶圓、半導體、晶圓代工、封測、IC設計、被動元件、PCB、載板、CCL、ABF、PTFE、HBM、CoWoS、
台積電、聯發科、鴻海、日月光、聯電、瑞昱、novatek、奇景、力積電、世界先進、環球晶、中美晶、
NVIDIA、AMD、Intel、Broadcom、Qualcomm、TSMC、Samsung、Micron、SK Hynix、
AI晶片、GPU、CPU、伺服器、資料中心、Blackwell、Hopper、Vera Rubin、CoWoS、HBM3E、
ETF、殖利率、本益比、EPS、ROE、毛利率、營收、法說會、財報、庫存、去化、
聯準會、升息、降息、通膨、CPI、非農、美債、殖利率曲線、
川普、關稅、貿易戰、地緣政治、
股癌、Gooaye、股海飯桶、KUMA、Wilson、
旺矽、中美晶、環球晶、台勝科、合晶、嘉晶、
台積電、聯發科、鴻海、廣達、緯創、英業達、仁寶、和碩、
日月光、矽品、京元電、欣銓、南茂、頎邦、
聯電、世界先進、力積電、華邦電、南亞科、
台光電、聯茂、EMC、楠梓電、滬科、耀華、
欣興、景碩、南電、燿華、定穎、台燿、
旺矽、久元、中華精測、穎崴、雙鴻、奇鋐、
瑞鼎、聯詠、奇景、矽創、天鈺、敦泰、
台達電、光寶科、士電、東元、
長榮、陽明、萬海、慧洋
"""


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
                prompt=WHISPER_PROMPT,
            )
        texts.append(result.text)
        os.unlink(part)

    return "\n".join(texts)
