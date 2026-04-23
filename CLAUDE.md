# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 本地執行
source .venv/bin/activate
python main.py

# 安裝套件
pip install requests feedparser openai anthropic python-dotenv
# 需要 ffmpeg（音檔壓縮）
brew install ffmpeg
```

GitHub Actions 自動執行，手動觸發：GitHub → Actions → Podcast 筆記自動整理 → Run workflow。

## Architecture

```
podcast-notes/
  config.py               # API keys、Podcast RSS 清單
  fetchers/rss.py         # 從 RSS 取得最新集資訊 + 下載音檔
  transcribe/whisper.py   # OpenAI Whisper API 轉錄（含 ffmpeg 壓縮與自動切段）
  notes/claude.py         # Claude 整理成結構化投資筆記
  publishers/line.py      # 推送摘要到 LINE；失敗時推錯誤通知
  storage/db.py           # SQLite 記錄已處理集數，防止重複轉錄
  main.py                 # 主流程：RSS → 下載 → Whisper → Claude → 存檔 → LINE
  outputs/                # 完整 Markdown 筆記（gitignore，僅本地）
```

**流程：** RSS 抓最新集 → 檢查是否已處理過（SQLite）→ 下載音檔 → ffmpeg 壓縮至 24MB 以下 → Whisper 轉逐字稿 → Claude 整理筆記 → 存 Markdown → 推 LINE 摘要 → 記錄已完成。

**筆記格式：** 本集主題、重點觀點（5-8條）、提到的股票/資產、總體經濟觀點、金句。

**LINE 推送：** 只推重點摘要版，完整筆記存在 `outputs/` 用 Obsidian 閱讀。

## Schedule（台灣時間）

| 時間 | 觸發 |
|------|------|
| 每週一 09:00 | `cron: "0 1 * * 1"` |
| 每週四 09:00 | `cron: "0 1 * * 4"` |

## Environment Variables

`.env`（本地）或 GitHub Secrets（CI）：

| 變數 | 用途 |
|------|------|
| `OPENAI_API_KEY` | Whisper API 轉錄，約 $0.36／集（1小時） |
| `ANTHROPIC_API_KEY` | Claude 整理筆記 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 推送 |
| `LINE_USER_ID` | 推送目標（與 line-news-bot、earnings-bot 相同） |

## Podcasts

| 節目 | RSS |
|------|-----|
| 股癌 Gooaye | `https://feeds.soundon.fm/podcasts/954689a5-3096-43a4-a80b-7810b219cef3.xml` |
| 股海飯桶 | `https://feeds.soundon.fm/podcasts/537b7401-756c-4d0d-b1df-36a49e2793d3.xml` |

新增節目：在 `config.py` 的 `PODCASTS` dict 加一行即可。

## Notes

- Whisper API 上限 25MB，超過自動用 ffmpeg 壓縮成 64kbps mono
- 若壓縮後仍超過則切成兩段分別轉錄再合併
- 失敗（餘額不足、API 錯誤等）會推 LINE 錯誤通知
- `storage/processed.db` 透過 GitHub Actions cache 跨 run 保存
