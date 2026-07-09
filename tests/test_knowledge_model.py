import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.knowledge_model_service import KnowledgeModelService


def test_knowledge_tree_and_source_registry():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        service = KnowledgeModelService(Path(temp_dir) / "app.sqlite3")
        source = service.register_source(
            domain_id="tia",
            title="TIA Portal public manual",
            url="https://example.com/manual",
            license_name="public-web-candidate",
            content="PLC diagnostic steps",
        )
        assert source["qualityStatus"] == "candidate"

        chapter = service.upsert_node(
            domain_id="tia",
            name="PLC 诊断基础",
            node_type="chapter",
            source_id=source["id"],
            quality_status="candidate",
        )
        node = service.upsert_node(
            domain_id="tia",
            parent_id=chapter["id"],
            name="硬件组态错误处理",
            node_type="operation",
            difficulty=4,
            exam_importance=2,
            engineering_importance=5,
            source_id=source["id"],
        )

        tree = service.list_tree("tia")
        assert len(tree) == 2
        assert node["engineeringImportance"] == 5
        assert service.list_sources("tia")[0]["id"] == source["id"]


def test_knowledge_model_rejects_invalid_quality_status():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        service = KnowledgeModelService(Path(temp_dir) / "app.sqlite3")
        try:
            service.upsert_node(domain_id="x", name="节点", quality_status="published")
        except ValueError as exc:
            assert "质量状态不支持" in str(exc)
        else:
            raise AssertionError("invalid quality status should fail")


if __name__ == "__main__":
    test_knowledge_tree_and_source_registry()
    test_knowledge_model_rejects_invalid_quality_status()
    print("PASS: test_knowledge_model")
