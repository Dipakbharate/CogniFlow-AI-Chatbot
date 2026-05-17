import sqlite3
import json
from datetime import datetime

class SQLiteMemory:
    def __init__(self, db_path="chatbot.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                history TEXT,
                updated_at TIMESTAMP,
                username TEXT DEFAULT 'default_user'
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                username TEXT PRIMARY KEY,
                preferences TEXT,
                updated_at TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id     TEXT,
                key         TEXT,
                value       TEXT,
                updated_at  TIMESTAMP,
                PRIMARY KEY (user_id, key)
            )
        ''')
        conn.commit()
        conn.close()

    def get_history(self, session_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT history FROM sessions WHERE session_id = ?', (session_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return []

    def update_history(self, session_id, role, content, username="default_user"):
        history = self.get_history(session_id)
        history.append({"role": role, "content": content})
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO sessions (session_id, history, updated_at, username)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                history=excluded.history,
                updated_at=excluded.updated_at,
                username=excluded.username
        ''', (session_id, json.dumps(history), datetime.now(), username))
        conn.commit()
        conn.close()

    def clear_history(self, session_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()

    def get_all_sessions(self, username=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if username:
            c.execute('SELECT session_id, history, updated_at FROM sessions WHERE username = ? ORDER BY updated_at DESC', (username,))
        else:
            c.execute('SELECT session_id, history, updated_at FROM sessions ORDER BY updated_at DESC')
        rows = c.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            session_id = row[0]
            try:
                history = json.loads(row[1])
            except:
                history = []
                
            # Get a short title from the first user message
            title = "New Chat"
            for msg in history:
                if msg["role"] == "user":
                    title = str(msg["content"])[:30] + ("..." if len(str(msg["content"])) > 30 else "")
                    break
                    
            sessions.append({
                "session_id": session_id,
                "title": title,
                "updated_at": row[2]
            })
        return sessions

    def get_user_preferences(self, username):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT preferences FROM user_profiles WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except:
                return {}
        return {}

    def update_user_preferences(self, username, preferences_dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO user_profiles (username, preferences, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                preferences=excluded.preferences,
                updated_at=excluded.updated_at
        ''', (username, json.dumps(preferences_dict), datetime.now()))
        conn.commit()
        conn.close()

    def save_user_fact(self, user_id, key, value):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO user_memory (user_id, key, value, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, key) DO UPDATE SET value=?, updated_at=datetime('now')
        """, (user_id, key, value, value))
        conn.commit()
        conn.close()

    def get_user_facts(self, user_id):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT key, value FROM user_memory WHERE user_id=?
        """, (user_id,)).fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
