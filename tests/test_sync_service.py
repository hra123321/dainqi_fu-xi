import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.sync_service import SyncService


def test_sync_push_and_pull_round_trip():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        service = SyncService(Path(temp_dir) / "app.sqlite3")
        pushed = service.push(
            "android-12",
            [
                {
                    "id": "event-1",
                    "type": "photo_task",
                    "payload": {"local_path": "queue/photo-1.jpg"},
                    "client_updated_at": 100,
                },
                {
                    "id": "bad",
                    "type": "unsupported",
                    "payload": {},
                },
            ],
        )
        assert pushed["accepted"] == ["event-1"]
        assert len(pushed["rejected"]) == 1

        pulled = service.pull("windows-main", since=0)
        assert pulled["success"] is True
        assert pulled["events"][0]["id"] == "event-1"
        assert pulled["events"][0]["payload"]["local_path"] == "queue/photo-1.jpg"


if __name__ == "__main__":
    test_sync_push_and_pull_round_trip()
    print("PASS: test_sync_service")
