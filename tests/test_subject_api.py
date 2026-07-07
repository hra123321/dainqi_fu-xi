import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from main import app


def test_subject_api_and_pages():
    client = TestClient(app)

    subjects_response = client.get("/api/subjects")
    assert subjects_response.status_code == 200
    subjects = subjects_response.json()["subjects"]
    assert len(subjects) >= 9
    assert any(item["name"] == "信号与系统" for item in subjects)

    page_response = client.get("/subjects")
    assert page_response.status_code == 200
    assert "新增自定义学科" in page_response.text

    search_response = client.get(
        "/api/knowledge/search",
        params={"query": "Fourier", "subject_id": "signals"},
    )
    assert search_response.status_code == 200
    assert "results" in search_response.json()


if __name__ == "__main__":
    test_subject_api_and_pages()
    print("PASS: test_subject_api")
