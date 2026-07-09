import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.subject_service import SubjectService


def test_subject_registry_create_and_topics():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        service = SubjectService(str(Path(temp_dir) / "app.sqlite3"))
        subject = service.create_subject(name="自动控制原理", short="自控", icon="🎛️")
        assert subject["name"] == "自动控制原理"
        assert subject["topic_count"] == 0

        count = service.replace_topics(
            subject["id"],
            [
                {"name": "传递函数", "difficulty": 4, "examImportance": 5, "engineeringImportance": 5},
                {"name": "根轨迹分析", "difficulty": 5, "examImportance": 4, "engineeringImportance": 5},
            ],
        )
        assert count == 2
        topics = service.get_topics(subject["id"])
        assert topics[0]["name"] == "传递函数"
        assert topics[0]["examImportance"] == 5


def test_subject_registry_duplicate_name():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        service = SubjectService(str(Path(temp_dir) / "app.sqlite3"))
        service.create_subject(name="电力电子技术")
        try:
            service.create_subject(name="电力电子技术")
        except ValueError as exc:
            assert "学科已存在" in str(exc)
        else:
            raise AssertionError("duplicate subject name should fail")


def test_learning_domain_create_and_validate_type():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        service = SubjectService(str(Path(temp_dir) / "app.sqlite3"))
        domain = service.create_domain(
            name="博图",
            domain_type="software",
            short="TIA",
            icon="🧰",
            version="V18",
            learning_goal="学习 PLC 工程诊断与项目维护",
        )
        assert domain["type"] == "software"
        assert domain["version"] == "V18"

        try:
            service.create_domain(name="未知类型", domain_type="unknown")
        except ValueError as exc:
            assert "学习领域类型不支持" in str(exc)
        else:
            raise AssertionError("unsupported domain type should fail")


if __name__ == "__main__":
    test_subject_registry_create_and_topics()
    test_subject_registry_duplicate_name()
    test_learning_domain_create_and_validate_type()
    print("PASS: test_subjects")
