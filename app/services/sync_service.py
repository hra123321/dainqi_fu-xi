"""多端增量同步服务。"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.ability_profile_service import ability_profile_service
from app.services.subject_service import subject_service


ALLOWED_SYNC_TYPES = {"wrong_question", "photo_task", "study_progress", "note"}


class SyncService:
    """为 Android 和 Windows 客户端提供最小可扩展同步协议。"""

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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_events (
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    client_updated_at INTEGER NOT NULL,
                    server_received_at INTEGER NOT NULL
                )
                """
            )

    def push(self, device_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        clean_device_id = device_id.strip()
        if not clean_device_id:
            raise ValueError("device_id 不能为空")

        accepted = []
        rejected = []
        now = int(time.time())
        with self._connect() as connection:
            for event in events:
                event_type = str(event.get("type", "")).strip()
                if event_type not in ALLOWED_SYNC_TYPES:
                    rejected.append({"event": event, "reason": f"不支持的同步事件类型：{event_type}"})
                    continue
                event_id = str(event.get("id") or f"evt_{uuid.uuid4().hex[:16]}")
                payload = event.get("payload") or {}
                client_updated_at = int(event.get("client_updated_at") or now)
                connection.execute(
                    """
                    INSERT OR REPLACE INTO sync_events
                    (id, device_id, event_type, payload_json, client_updated_at, server_received_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        clean_device_id,
                        event_type,
                        json.dumps(payload, ensure_ascii=False),
                        client_updated_at,
                        now,
                    ),
                )
                accepted.append(event_id)

        return {"success": True, "accepted": accepted, "rejected": rejected, "server_time": now}

    def pull(self, device_id: str, since: int = 0) -> dict[str, Any]:
        clean_device_id = device_id.strip()
        if not clean_device_id:
            raise ValueError("device_id 不能为空")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM sync_events
                WHERE server_received_at > ?
                ORDER BY server_received_at ASC
                """,
                (since,),
            ).fetchall()

        events = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
            events.append(item)

        now = int(time.time())
        return {
            "success": True,
            "device_id": clean_device_id,
            "server_time": now,
            "domains": subject_service.list_domains(include_topics=False),
            "ability_profile": ability_profile_service.build_profile(),
            "events": events,
        }


sync_service = SyncService()
