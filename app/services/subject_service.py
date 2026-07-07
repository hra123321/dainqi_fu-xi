"""学科注册服务。

这个模块负责保存“哪些学科可选”和“每个学科有哪些知识点”。
用 SQLite 而不是继续写死 JS，是因为自定义学科必须能持久保存。
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings


DEFAULT_ICON = "📘"


class SubjectService:
    """SQLite 版学科注册表。"""

    def __init__(self, db_path: str | None = None):
        self.db_path = Path(db_path or settings.APP_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_builtin_subjects()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    short TEXT NOT NULL DEFAULT '',
                    icon TEXT NOT NULL DEFAULT '📘',
                    aliases TEXT NOT NULL DEFAULT '[]',
                    source TEXT NOT NULL DEFAULT 'custom',
                    ingest_status TEXT NOT NULL DEFAULT 'not_started',
                    topic_count INTEGER NOT NULL DEFAULT 0,
                    question_count INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS subject_topics (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    difficulty INTEGER NOT NULL DEFAULT 3,
                    exam_importance INTEGER NOT NULL DEFAULT 3,
                    engineering_importance INTEGER NOT NULL DEFAULT 3,
                    source TEXT NOT NULL DEFAULT 'seed',
                    created_at INTEGER NOT NULL,
                    UNIQUE(subject_id, name),
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT '',
                    sources_found INTEGER NOT NULL DEFAULT 0,
                    sources_accepted INTEGER NOT NULL DEFAULT 0,
                    chunks_stored INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                );
                """
            )

    def _seed_builtin_subjects(self) -> None:
        seed_path = Path("data/subjects_seed.json")
        if not seed_path.exists():
            return

        with self._connect() as connection:
            existing = connection.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
            if existing:
                return

        seed_subjects = json.loads(seed_path.read_text(encoding="utf-8"))
        for subject in seed_subjects:
            created = self.create_subject(
                name=subject["name"],
                short=subject.get("short", ""),
                icon=subject.get("icon", DEFAULT_ICON),
                aliases=subject.get("aliases", []),
                source="seed",
                subject_id=subject.get("id"),
            )
            self.replace_topics(created["id"], subject.get("topics", []), source="seed")

    def create_subject(
        self,
        name: str,
        short: str = "",
        icon: str = DEFAULT_ICON,
        aliases: Optional[List[str]] = None,
        source: str = "custom",
        subject_id: Optional[str] = None,
    ) -> Dict:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("学科名称不能为空")

        now = int(time.time())
        subject_id = subject_id or self._make_subject_id(clean_name)
        aliases_json = json.dumps(aliases or [], ensure_ascii=False)

        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO subjects
                    (id, name, short, icon, aliases, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (subject_id, clean_name, short.strip(), icon or DEFAULT_ICON, aliases_json, source, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"学科已存在：{clean_name}") from exc

        return self.get_subject(subject_id, include_topics=True)

    def list_subjects(self, include_topics: bool = True) -> List[Dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM subjects ORDER BY source DESC, created_at ASC"
            ).fetchall()
        return [self._row_to_subject(row, include_topics=include_topics) for row in rows]

    def get_subject(self, subject_id: str, include_topics: bool = True) -> Dict:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if row is None:
            raise KeyError(f"学科不存在：{subject_id}")
        return self._row_to_subject(row, include_topics=include_topics)

    def get_topics(self, subject_id: str) -> List[Dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT name, difficulty, exam_importance, engineering_importance
                FROM subject_topics
                WHERE subject_id = ?
                ORDER BY created_at ASC, name ASC
                """,
                (subject_id,),
            ).fetchall()
        return [
            {
                "name": row["name"],
                "difficulty": row["difficulty"],
                "examImportance": row["exam_importance"],
                "engineeringImportance": row["engineering_importance"],
            }
            for row in rows
        ]

    def replace_topics(self, subject_id: str, topics: List[Dict], source: str = "generated") -> int:
        now = int(time.time())
        normalized_topics = []
        seen = set()
        for topic in topics:
            name = str(topic.get("name", "")).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            normalized_topics.append(
                (
                    uuid.uuid4().hex,
                    subject_id,
                    name,
                    self._star(topic.get("difficulty", 3)),
                    self._star(topic.get("examImportance", topic.get("exam_importance", 3))),
                    self._star(topic.get("engineeringImportance", topic.get("engineering_importance", 3))),
                    source,
                    now,
                )
            )

        with self._connect() as connection:
            connection.execute("DELETE FROM subject_topics WHERE subject_id = ?", (subject_id,))
            connection.executemany(
                """
                INSERT INTO subject_topics
                (id, subject_id, name, difficulty, exam_importance, engineering_importance, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                normalized_topics,
            )
            connection.execute(
                """
                UPDATE subjects
                SET topic_count = ?, updated_at = ?
                WHERE id = ?
                """,
                (len(normalized_topics), now, subject_id),
            )
        return len(normalized_topics)

    def update_subject_status(self, subject_id: str, ingest_status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE subjects SET ingest_status = ?, updated_at = ? WHERE id = ?",
                (ingest_status, int(time.time()), subject_id),
            )

    def create_job(self, subject_id: str) -> Dict:
        self.get_subject(subject_id, include_topics=False)
        now = int(time.time())
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_jobs
                (id, subject_id, status, stage, message, created_at, updated_at)
                VALUES (?, ?, 'queued', 'created', '等待开始入库', ?, ?)
                """,
                (job_id, subject_id, now, now),
            )
        return self.get_job(job_id)

    def update_job(self, job_id: str, **fields) -> Dict:
        allowed = {
            "status",
            "stage",
            "message",
            "sources_found",
            "sources_accepted",
            "chunks_stored",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        updates["updated_at"] = int(time.time())
        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [job_id]
        with self._connect() as connection:
            connection.execute(f"UPDATE ingestion_jobs SET {assignments} WHERE id = ?", values)
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Dict:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM ingestion_jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(f"入库任务不存在：{job_id}")
        return dict(row)

    def _row_to_subject(self, row: sqlite3.Row, include_topics: bool) -> Dict:
        subject = dict(row)
        subject["aliases"] = json.loads(subject.get("aliases") or "[]")
        subject["topics"] = self.get_topics(subject["id"]) if include_topics else []
        subject["courseLink"] = f"https://search.bilibili.com/all?keyword={subject['name']}+课程+教学"
        subject["courseName"] = f"{subject['name']}相关课程"
        return subject

    def _make_subject_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug or f"custom-{uuid.uuid4().hex[:8]}"

    def _star(self, value) -> int:
        try:
            number = int(value)
        except Exception:
            number = 3
        return max(1, min(5, number))


subject_service = SubjectService()
