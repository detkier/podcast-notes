import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "processed.db")


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS processed_episodes (
            audio_url TEXT PRIMARY KEY,
            podcast   TEXT,
            title     TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()


def already_processed(audio_url: str) -> bool:
    con = sqlite3.connect(DB_PATH)
    found = con.execute(
        "SELECT 1 FROM processed_episodes WHERE audio_url=?", (audio_url,)
    ).fetchone() is not None
    con.close()
    return found


def mark_processed(audio_url: str, podcast: str, title: str):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR IGNORE INTO processed_episodes (audio_url, podcast, title) VALUES (?,?,?)",
        (audio_url, podcast, title),
    )
    con.commit()
    con.close()
