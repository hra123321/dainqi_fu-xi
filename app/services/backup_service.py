"""本地数据备份与完整性检查服务。"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import zipfile
from pathlib import Path
from typing import Any

import chromadb

from app.config import settings


class BackupService:
    """为 SQLite 与 Chroma 本地数据生成可追溯备份。"""

    def __init__(
        self,
        app_db_path: str | Path | None = None,
        vector_db_path: str | Path | None = None,
        backup_dir: str | Path | None = None,
    ) -> None:
        self.app_db_path = Path(app_db_path or settings.APP_DB_PATH)
        self.vector_db_path = Path(vector_db_path or settings.VECTOR_DB_PATH)
        self.backup_dir = Path(backup_dir or "data/backups")

    def check_integrity(self) -> dict[str, Any]:
        """检查 SQLite 与 Chroma 是否可读。"""
        sqlite_status = self._check_sqlite()
        chroma_status = self._check_chroma()
        ok = sqlite_status["ok"] and chroma_status["ok"]
        return {
            "ok": ok,
            "sqlite": sqlite_status,
            "chroma": chroma_status,
        }

    def create_backup(self) -> dict[str, Any]:
        """创建 zip 备份，并写入 manifest 描述。"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / f"study-platform-backup-{timestamp}.zip"
        manifest = self._build_manifest()

        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )
            if self.app_db_path.exists():
                archive.write(self.app_db_path, "sqlite/app.sqlite3")
            if self.vector_db_path.exists():
                for file_path in self._iter_safe_files(self.vector_db_path):
                    archive.write(file_path, Path("chroma") / file_path.relative_to(self.vector_db_path))

        return {
            "ok": True,
            "backup_path": str(backup_path),
            "manifest": manifest,
        }

    def _build_manifest(self) -> dict[str, Any]:
        files = []
        for root in (self.app_db_path, self.vector_db_path):
            if root.is_file():
                files.append(self._file_manifest(root, root.name))
            elif root.exists():
                for file_path in self._iter_safe_files(root):
                    files.append(self._file_manifest(file_path, str(file_path.relative_to(root))))

        return {
            "created_at": int(time.time()),
            "format_version": 1,
            "app_db": str(self.app_db_path),
            "vector_db": str(self.vector_db_path),
            "chromadb_version": chromadb.__version__,
            "integrity": self.check_integrity(),
            "files": files,
        }

    def _check_sqlite(self) -> dict[str, Any]:
        if not self.app_db_path.exists():
            return {"ok": True, "exists": False, "message": "SQLite 数据库尚未创建"}
        try:
            with sqlite3.connect(self.app_db_path) as connection:
                result = connection.execute("PRAGMA quick_check").fetchone()[0]
            return {"ok": result == "ok", "exists": True, "quick_check": result}
        except Exception as exc:
            return {"ok": False, "exists": True, "error": str(exc)}

    def _check_chroma(self) -> dict[str, Any]:
        if not self.vector_db_path.exists():
            return {"ok": True, "exists": False, "collections": []}
        try:
            client = chromadb.PersistentClient(path=str(self.vector_db_path))
            collections = []
            for collection in client.list_collections():
                collections.append({"name": collection.name, "count": collection.count()})
            return {"ok": True, "exists": True, "collections": collections}
        except Exception as exc:
            return {"ok": False, "exists": True, "error": str(exc)}

    def _iter_safe_files(self, root: Path):
        for file_path in root.rglob("*"):
            if file_path.is_file() and file_path.name != ".env":
                yield file_path

    def _file_manifest(self, file_path: Path, relative_name: str) -> dict[str, Any]:
        return {
            "path": relative_name,
            "size": file_path.stat().st_size,
            "sha256": self._sha256(file_path),
        }

    def _sha256(self, file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
