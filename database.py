import sqlite3
import json

def get_db():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_allowed BOOLEAN DEFAULT 0
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

def add_user(user_id, username):
    with get_db() as db:
        db.execute("INSERT OR IGNORE INTO users (user_id, username, is_allowed) VALUES (?, ?, ?)", (user_id, username, 0))
        db.commit()

def is_user_allowed(user_id):
    with get_db() as db:
        res = db.execute("SELECT is_allowed FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return bool(res and res['is_allowed'])

def allow_user(user_id):
    with get_db() as db:
        db.execute("UPDATE users SET is_allowed = 1 WHERE user_id = ?", (user_id,))
        db.commit()

def add_message(user_id, role, content):
    with get_db() as db:
        db.execute("INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
        db.commit()

def get_history(user_id, limit=10):
    with get_db() as db:
        res = db.execute("SELECT role, content FROM (SELECT role, content, timestamp FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC", (user_id, limit)).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in res]
