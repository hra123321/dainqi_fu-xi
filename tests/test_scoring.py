import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.skills.exam_skills.scoring import is_answer_correct, parse_grading_result


def main():
    result = parse_grading_result("正确\n总分: 100\n过程完整。", "advanced")
    assert result["conclusion"] == "正确"
    assert result["score"] == 100
    assert is_answer_correct("a", "A") is True
    assert is_answer_correct("B", "A") is False
    print("PASS: test_scoring")


if __name__ == "__main__":
    main()
