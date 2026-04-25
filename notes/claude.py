from anthropic import Anthropic
from config import ANTHROPIC_API_KEY


def generate_notes(podcast_name: str, episode_title: str, transcript: str) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""你是投資筆記整理助手。以下是 Podcast「{podcast_name}」的集數「{episode_title}」的逐字稿。

整理前請先做以下校正：
- 「儲值股票」→「處置股票」（台股處置制度，Whisper 常誤辨）

請用繁體中文整理成結構化投資筆記，格式如下：

## 本集主題
（1-2 句話概述）

## 重點觀點
（條列 5-8 個核心觀點，每點說明清楚）

## 提到的股票/資產
（列出節目中提及的股票代號、ETF、資產類別，附上主持人的看法）

## 總體經濟觀點
（利率、通膨、景氣等宏觀看法，若無則略過）

## 金句
（1-3 句印象深刻的話）

---
逐字稿：
{transcript[:12000]}
"""
        }]
    )
    return msg.content[0].text
