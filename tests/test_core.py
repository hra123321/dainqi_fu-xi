import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config():
    from app.config import settings

    assert settings.MODEL_FLASH == "deepseek-v4-flash"
    assert settings.MODEL_PRO == "deepseek-v4-pro"
    assert settings.QUESTION_SESSION_TTL > 0
    print("PASS: config")


def test_dispatch():
    from app.models.dispatch import get_model_for_difficulty, is_pro_model

    assert get_model_for_difficulty("easy") == "deepseek-v4-flash"
    assert get_model_for_difficulty("hard") == "deepseek-v4-pro"
    assert is_pro_model("expert") is True
    assert is_pro_model("normal") is False
    print("PASS: dispatch")


def test_cache_key():
    from app.cache.cache_key import generate_cache_key, normalize_text

    assert normalize_text("  Hello  World  ") == "hello world"
    base = generate_cache_key("model", "system", "hello", extra_context="flash")
    changed = generate_cache_key("model", "system", "hello", extra_context="pro-thinking")
    assert base != changed
    print("PASS: cache_key")


def test_memory_cache():
    from app.cache.memory_cache import MemoryCache

    cache = MemoryCache(maxsize=3, ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    cache.get("a")
    cache.set("d", 4)
    assert cache.get("b") is None
    assert cache.get("d") == 4
    print("PASS: memory_cache")


def test_question_session():
    from app.services.question_session_service import QuestionSessionService

    service = QuestionSessionService(ttl_seconds=1)
    service.save_question(
        question_id="q1",
        question_text="测试题目",
        question_type="single_choice",
        difficulty="normal",
        answer="A",
        reference_answer="A",
        explanation="测试解析",
        knowledge_point="测试知识点",
        subject="测试学科",
    )
    assert service.get_question("q1") is not None
    time.sleep(1.1)
    assert service.get_question("q1") is None
    print("PASS: question_session")


def test_structured_questions_preserve_multipart():
    from app.services.exam_service import ExamService
    from app.services.question_session_service import question_session_service

    payload = {
        "questions": [
            {
                "question_text": (
                    "已知硅在 $T=300\\ \\text{K}$ 时的本征载流子浓度 $n_i = 1.5\\times10^{10}\\ \\text{cm}^{-3}$。\n"
                    "（1）计算 N 型硅中的电子浓度与空穴浓度；\n"
                    "（2）计算 P 型硅中的空穴浓度与电子浓度；\n"
                    "（3）若温度升高到 $T=400\\ \\text{K}$，重新计算并说明温度影响。"
                ),
                "type": "calculation",
                "options": [],
                "answer": "略",
                "reference_answer": "完整参考答案",
                "explanation": "完整解析",
            }
        ]
    }

    service = ExamService()
    questions = service._parse_questions(
        ai_text=json.dumps(payload, ensure_ascii=False),
        difficulty="hard",
        count=1,
        knowledge_point="半导体基础",
        subject="模拟电子技术",
    )

    assert len(questions) == 1
    assert "（3）" in questions[0]["question_text"]
    assert "\n（2）" in questions[0]["question_text"]
    session = question_session_service.get_question(questions[0]["id"])
    assert session is not None
    assert session.reference_answer == "完整参考答案"
    print("PASS: structured_questions")


def test_logger_stats():
    from app.utils.logger import get_stats

    stats = get_stats()
    assert "wrong_questions" in stats
    assert "api_errors" in stats
    assert "should_optimize" in stats
    print("PASS: logger_stats")


if __name__ == "__main__":
    tests = [
        test_config,
        test_dispatch,
        test_cache_key,
        test_memory_cache,
        test_question_session,
        test_structured_questions_preserve_multipart,
        test_logger_stats,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as error:
            print(f"FAIL: {test.__name__} - {error}")
            raise

    print(f"PASS: {passed}/{len(tests)}")
