import requests
import re
from config import LINE_TOKEN, LINE_USER_ID

MAX_CHARS = 4500


def push_message(text: str) -> bool:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}",
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}],
    }
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers, json=payload, timeout=10,
    )
    if resp.status_code == 200:
        print("  LINE 推送成功")
        return True
    else:
        print(f"  LINE 推送失敗：{resp.status_code} {resp.text}")
        return False


def _extract_section(notes: str, heading: str) -> str:
    """從 Markdown 筆記中抽出指定段落。"""
    pattern = rf"## {heading}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, notes, re.DOTALL)
    return match.group(1).strip() if match else ""


def push_error(podcast_name: str, episode_title: str, error: str) -> None:
    msg = (
        f"⚠️ Podcast 筆記失敗\n\n"
        f"節目：{podcast_name}\n"
        f"集數：{episode_title}\n\n"
        f"錯誤：{error[:200]}"
    )
    push_message(msg)


def push_podcast_notes(podcast_name: str, episode_title: str, notes: str) -> None:
    topic = _extract_section(notes, "本集主題")
    market = _extract_section(notes, "盤勢與市場動向")
    industry = _extract_section(notes, "產業分析")
    stocks = _extract_section(notes, "個股與資產")
    points = _extract_section(notes, "重點觀點")
    quote = _extract_section(notes, "金句")

    # 盤勢：只取條列行，最多 5 行
    market_lines = [l for l in market.splitlines() if l.strip().startswith(("-", "•", "**"))]
    market_short = "\n".join(market_lines[:5])

    # 產業分析：取各產業標題與第一行說明，最多 5 條
    industry_lines = [l for l in industry.splitlines() if l.strip().startswith(("###", "-", "•")) and l.strip() != "---"]
    industry_short = "\n".join(industry_lines[:8])

    # 個股：表格轉純文字，取名稱+看法欄，最多 6 檔
    stock_lines = [l for l in stocks.splitlines() if "|" in l and "---" not in l and "股票" not in l and "產品" not in l]
    stocks_short = "\n".join(
        "• " + " | ".join(c.strip() for c in l.split("|") if c.strip())[:80]
        for l in stock_lines[:6]
    )

    # 重點觀點：取前 5 條
    point_lines = [l for l in points.splitlines() if l.strip().startswith(("1.", "2.", "3.", "4.", "5.", "-", "**"))]
    points_short = "\n".join(point_lines[:8])

    # 金句：取第一條
    quote_line = next((l.strip().lstrip(">").strip() for l in quote.splitlines() if l.strip()), "")

    msg = f"🎙 {podcast_name}\n《{episode_title}》\n\n"
    msg += f"📌 本集主題\n{topic}\n\n"
    if market_short:
        msg += f"📊 盤勢\n{market_short}\n\n"
    if industry_short:
        msg += f"🏭 產業\n{industry_short}\n\n"
    if stocks_short:
        msg += f"📈 個股\n{stocks_short}\n\n"
    if points_short:
        msg += f"💡 重點觀點\n{points_short}\n\n"
    if quote_line:
        msg += f"💬 金句\n「{quote_line}」"

    if len(msg) > MAX_CHARS:
        msg = msg[:MAX_CHARS - 3] + "..."

    push_message(msg)
