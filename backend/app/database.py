import uuid
import aiosqlite
from typing import List, Dict, Any

class Database:
    def __init__(self, path: str = '/data/20_customer_segmentation_cdp.db'):
        self.path = path
        self._conn = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute('PRAGMA journal_mode=WAL')
        await self._conn.executescript('''
            CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, total_orders INTEGER DEFAULT 0, total_spent REAL DEFAULT 0, last_order_date TEXT, segment TEXT DEFAULT 'unknown', created_at TEXT DEFAULT (datetime('now')));
            CREATE TABLE IF NOT EXISTS customer_events (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, event_type TEXT NOT NULL, event_data TEXT, created_at TEXT DEFAULT (datetime('now')));
        ''')
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()
