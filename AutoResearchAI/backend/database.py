import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiosqlite
from backend.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Modular Database Manager.
    Uses aiosqlite for asynchronous SQLite operations.
    Follows repository pattern to allow seamless migration to PostgreSQL or SQLAlchemy later.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or settings.DATABASE_PATH)
        self._initialized = False

    async def ensure_db(self) -> None:
        """Ensure database tables exist before performing operations."""
        if not self._initialized:
            await self.init_db()

    async def init_db(self) -> None:
        """Initialize database tables and indexes."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS research_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        query_type TEXT DEFAULT 'General Automotive',
                        vehicles TEXT DEFAULT '[]',
                        summary TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        specifications TEXT DEFAULT '[]',
                        comparison TEXT DEFAULT NULL,
                        sources TEXT DEFAULT '[]',
                        key_findings TEXT DEFAULT '[]',
                        created_at TEXT NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query ON research_history(query)
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at ON research_history(created_at DESC)
                """)
                await db.commit()
                self._initialized = True
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def save_research(
        self,
        query: str,
        query_type: str,
        vehicles: List[str],
        summary: str,
        answer: str,
        specifications: List[Dict[str, Any]],
        comparison: Optional[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        key_findings: List[str]
    ) -> int:
        """Save a completed research session into the history table."""
        await self.ensure_db()
        created_at = datetime.utcnow().isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    INSERT INTO research_history (
                        query, query_type, vehicles, summary, answer,
                        specifications, comparison, sources, key_findings, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        query,
                        query_type,
                        json.dumps(vehicles),
                        summary,
                        answer,
                        json.dumps(specifications),
                        json.dumps(comparison) if comparison else None,
                        json.dumps(sources),
                        json.dumps(key_findings),
                        created_at
                    )
                )
                await db.commit()
                return cursor.lastrowid or 0
        except Exception as e:
            logger.error(f"Error saving research record: {e}")
            return 0

    async def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent research records."""
        await self.ensure_db()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT id, query, query_type, vehicles, summary, created_at
                    FROM research_history
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    result = []
                    for row in rows:
                        result.append({
                            "id": row["id"],
                            "query": row["query"],
                            "query_type": row["query_type"],
                            "vehicles": json.loads(row["vehicles"]) if row["vehicles"] else [],
                            "summary": row["summary"],
                            "created_at": row["created_at"]
                        })
                    return result
        except Exception as e:
            logger.error(f"Error reading history: {e}")
            return []

    async def get_research_by_id(self, research_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific full research session by ID."""
        await self.ensure_db()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM research_history WHERE id = ?",
                    (research_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return None
                    return {
                        "id": row["id"],
                        "query": row["query"],
                        "query_type": row["query_type"],
                        "vehicles": json.loads(row["vehicles"]) if row["vehicles"] else [],
                        "summary": row["summary"],
                        "answer": row["answer"],
                        "specifications": json.loads(row["specifications"]) if row["specifications"] else [],
                        "comparison": json.loads(row["comparison"]) if row["comparison"] else None,
                        "sources": json.loads(row["sources"]) if row["sources"] else [],
                        "key_findings": json.loads(row["key_findings"]) if row["key_findings"] else [],
                        "created_at": row["created_at"]
                    }
        except Exception as e:
            logger.error(f"Error fetching research ID {research_id}: {e}")
            return None

    async def find_cached_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Check if an identical query was researched recently (cache lookup)."""
        await self.ensure_db()
        clean_query = query.strip().lower()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM research_history WHERE LOWER(TRIM(query)) = ? ORDER BY id DESC LIMIT 1",
                    (clean_query,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return None
                    return {
                        "id": row["id"],
                        "query": row["query"],
                        "query_type": row["query_type"],
                        "vehicles": json.loads(row["vehicles"]) if row["vehicles"] else [],
                        "summary": row["summary"],
                        "answer": row["answer"],
                        "specifications": json.loads(row["specifications"]) if row["specifications"] else [],
                        "comparison": json.loads(row["comparison"]) if row["comparison"] else None,
                        "sources": json.loads(row["sources"]) if row["sources"] else [],
                        "key_findings": json.loads(row["key_findings"]) if row["key_findings"] else [],
                        "created_at": row["created_at"]
                    }
        except Exception as e:
            logger.error(f"Error in cache lookup: {e}")
            return None

    async def get_recent_sources(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve aggregated unique sources from past queries."""
        await self.ensure_db()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT sources FROM research_history ORDER BY id DESC LIMIT 20"
                ) as cursor:
                    rows = await cursor.fetchall()
                    seen_urls = set()
                    sources_list = []
                    for row in rows:
                        if row["sources"]:
                            try:
                                src_items = json.loads(row["sources"])
                                for s in src_items:
                                    if s.get("url") and s["url"] not in seen_urls:
                                        seen_urls.add(s["url"])
                                        sources_list.append(s)
                                        if len(sources_list) >= limit:
                                            return sources_list
                            except Exception:
                                pass
                    return sources_list
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return []

    async def check_connection(self) -> bool:
        """Health check for database connectivity."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT 1") as cursor:
                    val = await cursor.fetchone()
                    return val is not None and val[0] == 1
        except Exception:
            return False

# Global instance
db = DatabaseManager()
