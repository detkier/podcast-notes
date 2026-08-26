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


def _clean_markdown(text: str) -> str:
    """移除 Markdown 符號，保留純文字。"""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"^\s*#{1,3}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|\s*-+\s*\|.*", "", text)  # 移除表格分隔線
    return text.strip()


def push_podcast_notes(podcast_name: str, episode_title: str, notes: str) -> None:
    topic = _extract_section(notes, "本集主題")
    market = _extract_section(notes, "盤勢與市場動向")
    industry = _extract_section(notes, "產業分析")
    stocks = _extract_section(notes, "個股與資產")
    points = _extract_section(notes, "重點觀點")
    quote = _extract_section(notes, "金句")

    header = f"🎙 {podcast_name}｜《{episode_title}》\n\n"

    # 第一則：主題 + 盤勢 + 產業
    msg1 = header
    msg1 += f"📌 本集主題\n{topic}\n\n"
    if market:
        msg1 += f"📊 盤勢與市場動向\n{_clean_markdown(market)}\n\n"
    if industry:
        msg1 += f"🏭 產業分析\n{_clean_markdown(industry)}"
    if len(msg1) > MAX_CHARS:
        msg1 = msg1[:MAX_CHARS - 3] + "..."
    push_message(msg1)

    # 第二則：個股 + 重點觀點 + 金句
    msg2 = ""
    if stocks:
        # 個股：表格轉純文字
        stock_lines = [l for l in stocks.splitlines()
                       if l.strip() and "---" not in l and not l.strip().startswith("|股票") and not l.strip().startswith("|產品")]
        msg2 += f"📈 個股\n" + "\n".join(stock_lines) + "\n\n"
    if points:
        msg2 += f"💡 重點觀點\n{_clean_markdown(points)}\n\n"
    if quote:
        quote_line = next((l.strip().lstrip(">").strip() for l in quote.splitlines() if l.strip()), "")
        if quote_line:
            msg2 += f"💬 金句\n「{quote_line}」"
    if msg2:
        if len(msg2) > MAX_CHARS:
            msg2 = msg2[:MAX_CHARS - 3] + "..."
        push_message(msg2)
