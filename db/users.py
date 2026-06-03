import sqlite3
from datetime import datetime

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                joined_at TEXT,
                is_approved INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_news (
                url TEXT PRIMARY KEY,
                sent_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                added_at TEXT
            )
        """)

def add_user(user_id: int, username: str, auto_approve: bool = True):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, joined_at, is_approved) VALUES (?, ?, ?, ?)",
            (user_id, username, datetime.now().isoformat(), 1 if auto_approve else 0)
        )

def is_approved(user_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT is_approved FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return bool(row and row[0])

def is_news_sent(url: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT 1 FROM sent_news WHERE url = ?", (url,)
        ).fetchone() is not None

def mark_news_sent(url: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_news (url, sent_at) VALUES (?, ?)",
            (url, datetime.now().isoformat())
        )

def get_watchlist() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT ticker, name FROM watchlist ORDER BY added_at").fetchall()
        return [{"ticker": r[0], "name": r[1]} for r in rows]

def add_watchlist(ticker: str, name: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO watchlist (ticker, name, added_at) VALUES (?, ?, ?)",
            (ticker.upper(), name, datetime.now().isoformat())
        )

def remove_watchlist(ticker: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))

def clear_watchlist():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM watchlist")
