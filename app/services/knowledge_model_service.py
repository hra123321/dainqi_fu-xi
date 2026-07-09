"""学习领域的知识树与资料来源模型。"""

from __future__ import annotations

import hashlib
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import settings


NODE_TYPES = {"chapter", "knowledge", "operation", "error_case", "task"}
QUALITY_STATUSES = {"candidate", "approved", "rejected", "needs_review"}


class KnowledgeModelService:
    """管理知识节点、资料来源和发布状态。"""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or settings.APP_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    parent_id TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL,
                    node_type TEXT NOT NULL DEFAULT 'knowledge',
                    difficulty INTEGER NOT NULL DEFAULT 3,
                    exam_importance INTEGER NOT NULL DEFAULT 3,
                    engineering_importance INTEGER NOT NULL DEFAULT 3,
                    prerequisites TEXT NOT NULL DEFAULT '[]',
                    mastery REAL NOT NULL DEFAULT 0,
                    source_id TEXT NOT NULL DEFAULT '',
                    quality_status TEXT NOT NULL DEFAULT 'candidate',
                    version TEXT NOT NULL DEFAULT '',
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    UNIQUE(domain_id, parent_id, name)
                );

                CREATE TABLE IF NOT EXISTS knowledge_sources (
                    id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL DEFAULT '',
                    author TEXT NOT NULL DEFAULT '',
                    license TEXT NOT NULL DEFAULT '',
                    source_type TEXT NOT NULL DEFAULT 'web',
                    content_hash TEXT NOT NULL,
                    quality_status TEXT NOT NULL DEFAULT 'candidate',
                    discovered_at INTEGER NOT NULL,
                    reviewed_at INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE(domain_id, content_hash)
                );
                """
            )

    def upsert_node(
        self,
        domain_id: str,
        name: str,
        parent_id: str = "",
        node_type: str = "knowledge",
        difficulty: int = 3,
        exam_importance: int = 3,
        engineering_importance: int = 3,
        source_id: str = "",
        quality_status: str = "candidate",
        version: str = "",
    ) -> dict[str, Any]:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("知识节点名称不能为空")
        clean_node_type = self._validate(node_type, NODE_TYPES, "知识节点类型")
        clean_quality = self._validate(quality_status, QUALITY_STATUSES, "质量状态")
        now = int(time.time())
        node_id = self._make_id(domain_id, parent_id, clean_name)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_nodes
                (id, domain_id, parent_id, name, node_type, difficulty, exam_importance,
                 engineering_importance, source_id, quality_status, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain_id, parent_id, name) DO UPDATE SET
                    node_type = excluded.node_type,
                    difficulty = excluded.difficulty,
                    exam_importance = excluded.exam_importance,
                    engineering_importance = excluded.engineering_importance,
                    source_id = excluded.source_id,
                    quality_status = excluded.quality_status,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    node_id,
                    domain_id,
                    parent_id,
                    clean_name,
                    clean_node_type,
                    self._star(difficulty),
                    self._star(exam_importance),
                    self._star(engineering_importance),
                    source_id,
                    clean_quality,
                    version,
                    now,
                    now,
                ),
            )
        return self.get_node(node_id)

    def list_tree(self, domain_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM knowledge_nodes
                WHERE domain_id = ?
                ORDER BY parent_id ASC, created_at ASC, name ASC
                """,
                (domain_id,),
            ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def get_node(self, node_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM knowledge_nodes WHERE id = ?", (node_id,)).fetchone()
        if row is None:
            raise KeyError(f"知识节点不存在：{node_id}")
        return self._row_to_node(row)

    def register_source(
        self,
        domain_id: str,
        title: str,
        url: str = "",
        author: str = "",
        license_name: str = "",
        source_type: str = "web",
        content: str = "",
        quality_status: str = "candidate",
        metadata_json: str = "{}",
    ) -> dict[str, Any]:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("资料标题不能为空")
        clean_quality = self._validate(quality_status, QUALITY_STATUSES, "质量状态")
        content_hash = hashlib.sha256((url or content or clean_title).encode("utf-8")).hexdigest()
        source_id = f"src_{content_hash[:16]}"
        now = int(time.time())

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO knowledge_sources
                (id, domain_id, title, url, author, license, source_type, content_hash,
                 quality_status, discovered_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain_id, content_hash) DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url,
                    author = excluded.author,
                    license = excluded.license,
                    source_type = excluded.source_type,
                    quality_status = excluded.quality_status,
                    metadata_json = excluded.metadata_json
                """,
                (
                    source_id,
                    domain_id,
                    clean_title,
                    url.strip(),
                    author.strip(),
                    license_name.strip(),
                    source_type.strip() or "web",
                    content_hash,
                    clean_quality,
                    now,
                    metadata_json,
                ),
            )
        return self.get_source(source_id)

    def list_sources(self, domain_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM knowledge_sources WHERE domain_id = ? ORDER BY discovered_at DESC",
                (domain_id,),
            ).fetchall()
        return [self._row_to_source(row) for row in rows]

    def get_source(self, source_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM knowledge_sources WHERE id = ?", (source_id,)).fetchone()
        if row is None:
            raise KeyError(f"资料来源不存在：{source_id}")
        return self._row_to_source(row)

    def _row_to_node(self, row: sqlite3.Row) -> dict[str, Any]:
        node = dict(row)
        node["nodeType"] = node["node_type"]
        node["examImportance"] = node["exam_importance"]
        node["engineeringImportance"] = node["engineering_importance"]
        node["qualityStatus"] = node["quality_status"]
        return node

    def _row_to_source(self, row: sqlite3.Row) -> dict[str, Any]:
        source = dict(row)
        source["sourceType"] = source["source_type"]
        source["contentHash"] = source["content_hash"]
        source["qualityStatus"] = source["quality_status"]
        return source

    def _make_id(self, *parts: str) -> str:
        basis = "::".join(parts)
        return f"node_{hashlib.sha256(basis.encode('utf-8')).hexdigest()[:16]}"

    def _validate(self, value: str, allowed: set[str], label: str) -> str:
        clean_value = (value or "").strip().lower()
        if clean_value not in allowed:
            raise ValueError(f"{label}不支持：{value}")
        return clean_value

    def _star(self, value) -> int:
        try:
            number = int(value)
        except Exception:
            number = 3
        return max(1, min(5, number))


knowledge_model_service = KnowledgeModelService()
