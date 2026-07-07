"""
刷题路由 — 出题、提交、批改
"""

from fastapi import APIRouter

from app.models.schemas import (
    AnswerSubmitRequest,
    BatchGradeRequest,
    QuestionGenerateRequest,
)
from app.services.exam_service import exam_service


router = APIRouter(prefix="/api/exam", tags=["刷题"])


@router.post("/generate")
async def generate_questions(req: QuestionGenerateRequest):
    return await exam_service.generate_questions(
        knowledge_point=req.knowledge_point,
        difficulty=req.difficulty,
        count=req.count,
        subject=req.subject,
    )


@router.post("/explain")
async def explain_topic(req: dict):
    return await exam_service.explain_topic(
        topic=req.get("topic", ""),
        subject=req.get("subject", ""),
    )


@router.post("/submit")
async def submit_answer(req: AnswerSubmitRequest):
    return await exam_service.grade_answer(
        question_id=req.question_id,
        question=req.question,
        question_type=req.question_type,
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        reference_answer=req.reference_answer,
        knowledge_context=req.knowledge_context,
        subject=req.subject,
        knowledge_point=req.knowledge_point,
    )


@router.post("/grade")
async def grade_answers(req: BatchGradeRequest):
    if not req.answers:
        return {"results": [], "model_used": "none", "total": 0}

    results = []
    for answer_item in req.answers:
        result = await exam_service.grade_answer(
            question_id=answer_item.question_id,
            question=None,
            question_type=None,
            student_answer=answer_item.student_answer,
            subject=answer_item.subject or req.subject,
            knowledge_point=answer_item.knowledge_point or req.topic,
        )
        results.append(result)

    model_used = results[0].get("model_used", "flash") if results else "flash"
    return {"results": results, "model_used": model_used, "total": len(results)}
