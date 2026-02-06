import aiosqlite
import asyncio
from pathlib import Path
from typing import Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._init_tables()
        await self._conn.commit()

    async def _init_tables(self):
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0
            );
            """
        )
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_chars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                char_id TEXT,
                char_name TEXT,
                rarity TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """
        )

    async def ensure_user(self, user_id: int):
        await self._conn.execute(
            "INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, ?)",
            (user_id, 0),
        )
        await self._conn.commit()

    async def add_coins(self, user_id: int, amount: int):
        await self.ensure_user(user_id)
        await self._conn.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id)
        )
        await self._conn.commit()

    async def get_coins(self, user_id: int) -> int:
        await self.ensure_user(user_id)
        async with self._conn.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

    async def add_character(self, user_id: int, char):
        await self.ensure_user(user_id)
        await self._conn.execute(
            "INSERT INTO user_chars (user_id, char_id, char_name, rarity) VALUES (?, ?, ?, ?)",
            (user_id, char["id"], char["name"], char.get("rarity", "unknown")),
        )
        await self._conn.commit()

    async def list_user_chars(self, user_id: int):
        async with self._conn.execute(
            "SELECT char_id, char_name, rarity FROM user_chars WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchall()

    async def close(self):
        if self._conn:
            await self._conn.close()
