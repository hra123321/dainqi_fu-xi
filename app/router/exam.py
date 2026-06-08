"""
============================================
 刷题路由 — 出题、提交、批改
============================================
"""

from fastapi import APIRouter
from app.models.schemas import QuestionGenerateRequest, AnswerSubmitRequest, GradingResult
from app.services.exam_service import exam_service

# 创建路由组，所有接口前缀 /api/exam
router = APIRouter(prefix="/api/exam", tags=["刷题"])


@router.post("/generate")
async def generate_questions(req: QuestionGenerateRequest):
    """
    【出题接口】
    
    请求示例:
        POST /api/exam/generate
        {"knowledge_point": "欧姆定律", "difficulty": "easy", "count": 3}
    
    返回:
        {"questions": [...], "knowledge_context": "...", "model_used": "flash"}
    """
    result = await exam_service.generate_questions(
        knowledge_point=req.knowledge_point,
        difficulty=req.difficulty,
        count=req.count,
    )
    return result




@router.post("/explain")
async def explain_topic(req: dict):
    """
    ?????????
    
    ????:
        POST /api/exam/explain
        {"topic": "?????", "subject": "????"}
    
    ??:
        {"topic": "...", "subject": "...", "explanation": "...", "knowledge_context": "..."}
    """
    result = await exam_service.explain_topic(
        topic=req.get("topic", ""),
        subject=req.get("subject", ""),
    )
    return result

@router.post("/submit")
async def submit_answer(req: AnswerSubmitRequest):
    """
    【提交答案接口】
    
    请求示例:
        POST /api/exam/submit
        {
            "question_id": "q_abc123",
            "question_type": "objective",
            "question": "...",
            "student_answer": "...",
            "correct_answer": "..."
        }
    
    返回:
        {"score": 100, "conclusion": "正确", "analysis": "...", "model_used": "flash"}
    """
    result = await exam_service.grade_answer(
        question_id=req.question_id,
        question=req.question,
        question_type=req.question_type,
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        reference_answer=req.reference_answer,
        knowledge_context=req.knowledge_context,
    )
    return result

@router.post("/grade")
async def grade_answers(req: dict):
    """
    【批量批改接口】
    一次性批改多道题的答案

    请求示例:
        POST /api/exam/grade
        {"topic": "欧姆定律", "subject": "电路理论", "answers": [...]}

    返回:
        {"results": [...], "model_used": "...", "total": 5}
    """
    answers = req.get("answers", [])
    if not answers:
        return {"results": [], "model_used": "none", "total": 0}

    results = []
    for ans in answers:
        result = await exam_service.grade_answer(
            question_id=ans.get("question_id", ""),
            question=ans.get("question", ""),
            question_type=ans.get("question_type", "objective"),
            student_answer=ans.get("student_answer", ""),
            correct_answer=ans.get("correct_answer"),
            reference_answer=ans.get("reference_answer"),
            knowledge_context=ans.get("knowledge_context", ""),
        )
        results.append(result)

    model_used = results[0].get("model_used", "flash") if results else "flash"
    return {"results": results, "model_used": model_used, "total": len(results)}
