"""SQLite-Datenbank für Interaktionen und Wissen."""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from core.config import MEMORY_DB_PATH
from core.logger import get_logger

_logger = get_logger(__name__)


@dataclass
class Interaction:
    timestamp: str
    role: str
    content: str
    meta: Optional[str]


@dataclass
class Fact:
    timestamp: str
    source: str
    fact: str
    importance: int


class MemoryDB:
    """Minimaler SQLite-Wrapper für Gesprächs- und Wissensspeicher."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or MEMORY_DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    source TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    importance INTEGER DEFAULT 1
                )
                """
            )
            self._conn.commit()

    def add_interaction(self, role: str, content: str, meta: str | None = None) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO interactions (ts, role, content, meta) VALUES (?, ?, ?, ?)",
                (datetime.utcnow().isoformat(), role, content, meta),
            )
            self._conn.commit()
        _logger.info("Interaktion gespeichert (%s)", role)

    def add_fact(self, source: str, fact: str, importance: int = 1) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO facts (ts, source, fact, importance) VALUES (?, ?, ?, ?)",
                (datetime.utcnow().isoformat(), source, fact, importance),
            )
            self._conn.commit()
        _logger.info("Fakt gespeichert (%s)", source)

    def get_recent_interactions(self, limit: int = 50) -> List[Interaction]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT ts, role, content, meta FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [Interaction(row["ts"], row["role"], row["content"], row["meta"]) for row in rows]

    def get_facts(self, minimum_importance: int = 1) -> List[Fact]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT ts, source, fact, importance FROM facts WHERE importance >= ? ORDER BY importance DESC, id DESC",
                (minimum_importance,),
            )
            rows = cur.fetchall()
        return [Fact(row["ts"], row["source"], row["fact"], row["importance"]) for row in rows]

    def iter_interactions(self) -> Iterable[Interaction]:
        with self._lock:
            cur = self._conn.cursor()
            rows = list(cur.execute("SELECT ts, role, content, meta FROM interactions ORDER BY id"))
        for row in rows:
            yield Interaction(row["ts"], row["role"], row["content"], row["meta"])

    def close(self) -> None:
        with self._lock:
            self._conn.close()
