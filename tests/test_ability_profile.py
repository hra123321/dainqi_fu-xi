import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ability_profile_service import AbilityProfileService


def test_ability_profile_groups_by_subject_topic_and_error_type():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        wrong_file = Path(temp_dir) / "wrong.jsonl"
        records = [
            {
                "subject": "模拟电子技术",
                "knowledge_point": "静态工作点",
                "difficulty": "hard",
                "analysis": "公式代入错误，单位处理不严谨",
                "question_type": "advanced",
            },
            {
                "subject": "模拟电子技术",
                "knowledge_point": "静态工作点",
                "difficulty": "normal",
                "analysis": "计算结果错误",
                "question_type": "objective",
            },
            {
                "subject": "信号与系统",
                "knowledge_point": "卷积积分",
                "difficulty": "expert",
                "analysis": "审题遗漏条件",
                "question_type": "advanced",
            },
        ]
        with wrong_file.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        profile = AbilityProfileService(wrong_file).build_profile()

        assert profile["totalWrong"] == 3
        assert profile["weakestNodes"][0]["knowledgePoint"] == "静态工作点"
        assert profile["errorTypeDistribution"]["formula"] == 1
        assert profile["subjects"][0]["subject"] == "模拟电子技术"
        assert profile["subjects"][0]["weakNodes"][0]["reviewPriority"] > 0


if __name__ == "__main__":
    test_ability_profile_groups_by_subject_topic_and_error_type()
    print("PASS: test_ability_profile")
