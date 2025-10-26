import sqlite3
import json
from typing import Optional, Dict

DB_PATH = '/data/queue.db'

class PersistentQueue:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def push(self, payload: Dict):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('INSERT INTO queue (payload, status) VALUES (?, ?)', (json.dumps(payload, ensure_ascii=False), 'queued'))
        conn.commit()
        conn.close()

    def pop(self) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, payload FROM queue WHERE status='queued' ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        id_, payload = row
        cur.execute("UPDATE queue SET status='processing' WHERE id=?", (id_,))
        conn.commit()
        conn.close()
        return {'id': id_, 'payload': json.loads(payload)}

    def mark_done(self, id_):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE queue SET status='done' WHERE id=?", (id_,))
        conn.commit()
        conn.close()

    def mark_failed(self, id_, note=''):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE queue SET status='failed' WHERE id=?", (id_,))
        conn.commit()
        conn.close()