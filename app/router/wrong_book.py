"""
错题本路由
"""
from fastapi import APIRouter, Query
from app.services.wrong_book_service import wrong_book_service

router = APIRouter(prefix="/api/wrong-book", tags=["错题本"])

@router.get("/questions")
async def get_wrong_questions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    difficulty: str = None,
    knowledge_point: str = None,
    sort_by: str = "newest",
):
    return wrong_book_service.get_all_wrong_questions(
        limit=limit, offset=offset,
        difficulty=difficulty, knowledge_point=knowledge_point,
        sort_by=sort_by,
    )

@router.get("/analysis")
async def get_analysis():
    return wrong_book_service.get_analysis()

@router.get("/ability-profile")
async def get_ability_profile():
    return wrong_book_service.get_ability_profile()

@router.post("/evolve")
async def trigger_evolve():
    return await wrong_book_service.auto_evolve()

@router.delete("/clear")
async def clear_wrong_questions():
    ok = wrong_book_service.clear_wrong_questions()
    return {"success": ok, "message": "错题本已清空" if ok else "清空失败"}
