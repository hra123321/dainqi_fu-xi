"""
============================================
 管理路由 — 系统状态、日志查看
============================================
"""

from fastapi import APIRouter
from app.utils.logger import logger, get_stats, get_recent_wrong_questions
from app.cache.memory_cache import cache

router = APIRouter(prefix="/api/admin", tags=["管理"])


@router.get("/status")
async def get_system_status():
    """
    【系统状态】
    
    返回系统各模块的运行状态和统计数据。
    """
    from app.prompts.loader import get_prompt_count
    from app.vector_db.client import vector_db
    
    return {
        "version": "1.0.0",
        "prompts_loaded": get_prompt_count(),
        "cache_stats": cache.stats,
        "log_stats": get_stats(),
        "collections": vector_db.get_all_collections(),
    }


@router.get("/logs/wrong-questions")
async def get_wrong_questions():
    """
    【查看错题记录】
    
    返回最近的错题数据，用于分析和调试。
    """
    questions = get_recent_wrong_questions(limit=50)
    return {"count": len(questions), "questions": questions}


@router.get("/stats")
async def get_log_stats():
    """
    【日志统计】
    
    返回错题和异常的统计数据。
    """
    return get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """
    【清空缓存】
    
    手动清空内存缓存（调试用）。
    """
    cache.clear()
    return {"message": "缓存已清空", "cache_stats": cache.stats}
