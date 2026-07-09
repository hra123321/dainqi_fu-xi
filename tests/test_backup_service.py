import json
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.backup_service import BackupService


def test_backup_service_checks_integrity_and_excludes_env():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        root = Path(temp_dir)
        sqlite_path = root / "app.sqlite3"
        vector_path = root / "vector_db"
        backup_dir = root / "backups"

        with sqlite3.connect(sqlite_path) as connection:
            connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
            connection.execute("INSERT INTO demo (name) VALUES ('ok')")

        vector_path.mkdir()
        (vector_path / "index.txt").write_text("vector placeholder", encoding="utf-8")
        (vector_path / ".env").write_text("sk-should-not-be-backed-up", encoding="utf-8")

        service = BackupService(sqlite_path, vector_path, backup_dir)
        integrity = service.check_integrity()
        assert integrity["sqlite"]["ok"] is True

        result = service.create_backup()
        assert result["ok"] is True
        backup_path = Path(result["backup_path"])
        assert backup_path.exists()

        with zipfile.ZipFile(backup_path) as archive:
            names = set(archive.namelist())
            assert "manifest.json" in names
            assert "sqlite/app.sqlite3" in names
            assert "chroma/index.txt" in names
            assert "chroma/.env" not in names
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        assert manifest["format_version"] == 1
        assert any(item["path"] == "app.sqlite3" for item in manifest["files"])


if __name__ == "__main__":
    test_backup_service_checks_integrity_and_excludes_env()
    print("PASS: test_backup_service")
