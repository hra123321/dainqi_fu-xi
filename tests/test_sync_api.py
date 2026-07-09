import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from main import app


def test_sync_api_push_pull():
    client = TestClient(app)
    push_response = client.post(
        "/api/v1/sync/push",
        json={
            "device_id": "android-test",
            "events": [
                {
                    "id": "api-sync-event",
                    "type": "study_progress",
                    "payload": {"domain_id": "signals", "progress": 0.5},
                    "client_updated_at": 100,
                }
            ],
        },
    )
    assert push_response.status_code == 200
    assert push_response.json()["accepted"] == ["api-sync-event"]

    pull_response = client.post(
        "/api/v1/sync/pull",
        json={"device_id": "android-test", "since": 0},
    )
    assert pull_response.status_code == 200
    payload = pull_response.json()
    assert "domains" in payload
    assert "ability_profile" in payload
    assert any(event["id"] == "api-sync-event" for event in payload["events"])


if __name__ == "__main__":
    test_sync_api_push_pull()
    print("PASS: test_sync_api")
