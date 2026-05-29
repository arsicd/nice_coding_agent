import asyncio
from pathlib import Path

import sqlite3

from core.config import settings

ROOT_DIR = settings.project_root
DB_FILES_DIR = ROOT_DIR / ".nice" / "db_files"
OVERVIEW_CACHE_DB_PATH = DB_FILES_DIR / "overview_cache.sqlite"


class OverviewCache:
    def __init__(self, db_path: Path = OVERVIEW_CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._db_lock = asyncio.Lock()

    def _init_db(self):
        DB_FILES_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_overviews (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT,
                    summary TEXT
                )
            """)

    async def get_cached_overview(
        self, file_path: str, file_hash: str | None = None
    ) -> str | None:
        return await asyncio.to_thread(self._get_cached_overview, file_path, file_hash)

    def _get_cached_overview(
        self, file_path: str, file_hash: str | None = None
    ) -> str | None:
        query = "SELECT summary FROM file_overviews WHERE file_path = ?"
        params = (file_path,)
        if file_hash:
            query += " AND file_hash = ?"
            params = (file_path, file_hash)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else None

    async def set_cached_overview(self, file_path: str, file_hash: str, summary: str):
        async with self._db_lock:
            await asyncio.to_thread(
                self._set_cached_overview, file_path, file_hash, summary
            )

    def _set_cached_overview(self, file_path: str, file_hash: str, summary: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO file_overviews (file_path, file_hash, summary) VALUES (?, ?, ?)",
                (file_path, file_hash, summary),
            )

    def is_empty(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM file_overviews")
            row = cursor.fetchone()
            return not bool(row[0]) if row else True
