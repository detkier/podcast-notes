import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

OPENAI_THRESHOLD = 5.0    # 低於 $5 USD 警告
ANTHROPIC_THRESHOLD = 5.0 # 低於 $5 USD 警告


def push_line(text: str):
    requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"},
        json={"to": LINE_USER_ID, "messages": [{"type": "text", "text": text}]},
        timeout=10,
    )


def check_openai():
    resp = requests.get(
        "https://api.openai.com/dashboard/billing/credit_grants",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"OpenAI 餘額查詢失敗：{resp.status_code}")
        return None
    data = resp.json()
    remaining = data.get("total_available", 0)
    print(f"OpenAI 餘額：${remaining:.2f}")
    return remaining


def check_anthropic():
    resp = requests.get(
        "https://api.anthropic.com/v1/organizations/billing/credit_grants",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"Anthropic 餘額查詢失敗：{resp.status_code}")
        return None
    data = resp.json()
    # 加總所有未過期的 credit grant
    remaining = sum(
        g.get("remaining_units", 0) / 1_000_000  # 單位換算為 USD
        for g in data.get("data", [])
        if g.get("status") == "active"
    )
    print(f"Anthropic 餘額：${remaining:.2f}")
    return remaining


def main():
    warnings = []

    openai_balance = check_openai()
    if openai_balance is not None and openai_balance < OPENAI_THRESHOLD:
        warnings.append(f"OpenAI（Whisper）剩餘 ${openai_balance:.2f} USD，請盡快儲值！")

    anthropic_balance = check_anthropic()
    if anthropic_balance is not None and anthropic_balance < ANTHROPIC_THRESHOLD:
        warnings.append(f"Anthropic（Claude）剩餘 ${anthropic_balance:.2f} USD，請盡快儲值！")

    if warnings:
        msg = "⚠️ API 餘額不足警告\n\n" + "\n".join(warnings)
        push_line(msg)
        print("已推送 LINE 通知")
    else:
        print("餘額正常，無需通知")


if __name__ == "__main__":
    main()
