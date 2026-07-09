import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.growth_gate_service import GrowthGateService
from app.services.knowledge_model_service import KnowledgeModelService


def test_growth_gate_approves_open_source_candidate():
    service = GrowthGateService()
    result = service.evaluate_source(
        {
            "title": "公开课程资料",
            "license": "public-web-candidate",
            "contentHash": "a" * 64,
            "url": "https://example.edu/open-course",
        }
    )
    assert result.passed is True
    assert result.status == "approved"


def test_growth_gate_requires_review_for_unclear_license():
    service = GrowthGateService()
    result = service.evaluate_source(
        {
            "title": "来源不明资料",
            "license": "",
            "contentHash": "b" * 64,
            "url": "https://example.com/file",
        }
    )
    assert result.passed is False
    assert result.status == "needs_review"


def test_quality_update_methods_round_trip():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        model = KnowledgeModelService(Path(temp_dir) / "app.sqlite3")
        source = model.register_source(
            domain_id="signals",
            title="公开资料",
            url="https://example.com/open",
            license_name="public-web-candidate",
            content="source",
        )
        updated = model.update_source_quality(source["id"], "approved")
        assert updated["qualityStatus"] == "approved"

        node = model.upsert_node(domain_id="signals", name="卷积积分")
        updated_node = model.update_node_quality(node["id"], "needs_review")
        assert updated_node["qualityStatus"] == "needs_review"


if __name__ == "__main__":
    test_growth_gate_approves_open_source_candidate()
    test_growth_gate_requires_review_for_unclear_license()
    test_quality_update_methods_round_trip()
    print("PASS: test_growth_gate")
