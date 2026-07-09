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

    domain_response = client.get("/api/v1/domains")
    assert domain_response.status_code == 200
    assert "domains" in domain_response.json()

    create_response = client.post(
        "/api/v1/domains",
        json={
            "name": "博图测试领域",
            "domain_type": "software",
            "short": "TIA",
            "icon": "🧰",
            "version": "V18",
            "learning_goal": "复习 PLC 项目诊断、手册阅读和错误处理",
        },
    )
    assert create_response.status_code in (200, 409)
    if create_response.status_code == 200:
        domain = create_response.json()["domain"]
        assert domain["type"] == "software"
    else:
        domain = next(item for item in client.get("/api/v1/domains").json()["domains"] if item["name"] == "博图测试领域")

    source_response = client.post(
        "/api/v1/sources",
        json={
            "domain_id": domain["id"],
            "title": "博图公开手册候选",
            "url": "https://example.com/tia-manual",
            "license_name": "public-web-candidate",
            "content": "PLC 诊断资料摘要",
        },
    )
    assert source_response.status_code in (200, 409)

    node_response = client.post(
        f"/api/v1/domains/{domain['id']}/knowledge-tree",
        json={
            "name": "PLC 硬件组态诊断",
            "node_type": "operation",
            "difficulty": 4,
            "exam_importance": 2,
            "engineering_importance": 5,
        },
    )
    assert node_response.status_code == 200

    tree_response = client.get(f"/api/v1/domains/{domain['id']}/knowledge-tree")
    assert tree_response.status_code == 200
    assert tree_response.json()["nodes"]


if __name__ == "__main__":
    test_subject_api_and_pages()
    print("PASS: test_subject_api")
