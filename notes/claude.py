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
- 「戲劇院」→「矽晶圓」（Whisper 發音誤辨）
- 「秀蘭集團」→「中美晶集團」（Whisper 誤辨公司名稱）
- 「旺西」→「旺矽」（旺矽科技，Whisper 誤辨）
- 「KOHAS」→「CoWoS」（台積電先進封裝技術，Whisper 誤辨）

請用繁體中文整理成結構化投資筆記，格式如下：

## 本集主題
（1-2 句話概述）

## 盤勢與市場動向
（本集對大盤、指數、整體市場氣氛的看法；提到的重要事件、政策、總經數據對盤面的影響）

## 產業分析
（詳細列出提到的產業或族群，說明主持人的看法、潛在機會或風險，每個產業至少 2-3 句）

## 個股與資產
（列出所有提及的股票代號與名稱、ETF、資產，附上主持人的具體看法、目標價或操作建議，若有的話）

## 重點觀點
（條列 5-8 個核心觀點，每點說明清楚）

## 總體經濟觀點
（利率、通膨、景氣、匯率等宏觀看法，若無則略過）

## 金句
（1-3 句印象深刻的話）

---
逐字稿：
{transcript[:12000]}
"""
        }]
    )
    return msg.content[0].text
