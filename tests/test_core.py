"""
============================================
 核心功能快速测试 — 验证所有模块是否正常
============================================
运行方式: python -m pytest tests/test_core.py -v
或直接: python tests/test_core.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_config():
    """测试配置模块"""
    from app.config import settings
    assert settings.MODEL_FLASH == "deepseek-v4-flash"
    assert settings.MODEL_PRO == "deepseek-v4-pro"
    assert settings.MEMORY_CACHE_TTL == 300
    print("  PASS: config")


def test_dispatch():
    """测试模型调度"""
    from app.models.dispatch import get_model_for_difficulty, is_pro_model
    assert get_model_for_difficulty("easy") == "deepseek-v4-flash"
    assert get_model_for_difficulty("hard") == "deepseek-v4-pro"
    assert is_pro_model("expert") == True
    assert is_pro_model("normal") == False
    print("  PASS: dispatch")


def test_cache_key():
    """测试缓存键生成"""
    from app.cache.cache_key import normalize_text, generate_cache_key
    assert normalize_text("  Hello  World  ") == "hello world"
    k1 = generate_cache_key("model", "system", "hello")
    k2 = generate_cache_key("model", "system", "hello")
    assert k1 == k2
    print("  PASS: cache_key")


def test_memory_cache():
    """测试内存缓存"""
    from app.cache.memory_cache import MemoryCache
    c = MemoryCache(maxsize=3, ttl=60)
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3)
    c.get("a")
    c.set("d", 4)
    assert c.get("b") is None  # b should be evicted (LRU)
    assert c.get("d") == 4
    print("  PASS: memory_cache")


def test_prompts():
    """测试提示词加载"""
    from app.prompts.loader import load_prompts, get_prompt, list_prompts
    load_prompts()
    names = list_prompts()
    assert "general" in names
    assert "objective_mcq" in names
    assert "advanced_answer" in names
    assert "skill_optimize" in names
    text = get_prompt("general", question="测试", knowledge_context="测试")
    assert "测试" in text
    print("  PASS: prompts")


def test_vector_db():
    """测试向量数据库"""
    from app.vector_db.client import vector_db, ALL_COLLECTIONS
    for name in ALL_COLLECTIONS:
        col = vector_db.get_or_create_collection(name)
        assert col is not None
    stats = vector_db.get_all_collections()
    assert len(stats) == 4
    print("  PASS: vector_db")


def test_logger():
    """测试日志模块"""
    from app.utils.logger import get_stats
    stats = get_stats()
    assert "wrong_questions" in stats
    assert "api_errors" in stats
    print("  PASS: logger")


def test_skills():
    """测试 Skill 模块"""
    from app.skills.vector_skills.chunk_strategy import smart_chunk, validate_chunks
    from app.skills.exam_skills.scoring import parse_grading_result
    
    chunks = smart_chunk(["第一段", "第二段"], chunk_size=100)
    assert len(chunks) > 0
    
    result = parse_grading_result("正确！回答得很好", "objective")
    assert result["conclusion"] == "正确"
    print("  PASS: skills")


if __name__ == "__main__":
    print("=== 核心功能测试 ===")
    tests = [
        test_config, test_dispatch, test_cache_key,
        test_memory_cache, test_prompts, test_vector_db,
        test_logger, test_skills,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__} - {e}")
    print(f"\n=== {passed}/{len(tests)} 测试通过 ===")
