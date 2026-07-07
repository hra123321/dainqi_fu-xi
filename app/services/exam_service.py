"""
刷题业务服务 — 业务逻辑编排
"""

import json
import uuid
from typing import Dict, List, Optional

from app.models.dispatch import get_model_for_difficulty
from app.models.schemas import GeneratedQuestionSet
from app.services.ai_service import ai_service
from app.services.question_session_service import question_session_service
from app.utils.logger import logger, record_wrong_question
from app.vector_db.retriever import retriever


class ExamService:
    """组合 AI 调用、知识检索、题目会话和错题记录。"""

    async def generate_questions(
        self,
        knowledge_point: str,
        difficulty: str = "normal",
        count: int = 5,
        subject: str = "",
    ) -> Dict:
        logger.info(f"[出题] 知识点={knowledge_point} 难度={difficulty} 数量={count}")

        search_result = retriever.search(knowledge_point, top_k=5)
        context = retriever.format_context(search_result)
        model_used = get_model_for_difficulty(difficulty)

        ai_response = await self._generate_question_payload(
            difficulty=difficulty,
            knowledge_point=knowledge_point,
            subject=subject,
            count=count,
            context=context,
        )

        questions = self._parse_questions(
            ai_text=ai_response,
            difficulty=difficulty,
            count=count,
            knowledge_point=knowledge_point,
            subject=subject,
        )

        context_preview = context[:500] + "..." if len(context) > 500 else context
        return {
            "questions": questions,
            "knowledge_context": context_preview,
            "model_used": model_used,
        }

    async def grade_answer(
        self,
        question_id: str,
        question: Optional[str],
        question_type: Optional[str],
        student_answer: str,
        correct_answer: Optional[str] = None,
        reference_answer: Optional[str] = None,
        knowledge_context: str = "",
        subject: str = "",
        knowledge_point: str = "",
    ) -> Dict:
        logger.info(f"[批改] {question_id} | 题型={question_type or 'auto'}")

        session = question_session_service.get_question(question_id)
        resolved = self._resolve_question_payload(
            session=session,
            fallback_question=question or "",
            fallback_type=question_type or "objective",
            fallback_correct_answer=correct_answer or "",
            fallback_reference_answer=reference_answer or "",
            fallback_knowledge_point=knowledge_point,
            fallback_subject=subject,
        )

        if resolved["submit_type"] == "objective":
            prompt_name = "objective_mcq"
            difficulty = "easy"
            prompt_kwargs = {
                "question": resolved["question"],
                "correct_answer": resolved["correct_answer"],
                "student_answer": student_answer,
                "knowledge_context": knowledge_context,
            }
        else:
            prompt_name = "advanced_answer"
            difficulty = "hard"
            prompt_kwargs = {
                "question": resolved["question"],
                "reference_answer": resolved["reference_answer"],
                "student_answer": student_answer,
                "knowledge_context": knowledge_context,
            }

        ai_response = await ai_service.call(
            prompt_name=prompt_name,
            difficulty=difficulty,
            **prompt_kwargs,
        )

        model_used = get_model_for_difficulty(difficulty)
        result = self._parse_grading(ai_response, resolved["submit_type"])

        is_correct = result.get("conclusion", "").strip() == "正确"
        if not is_correct:
            record_wrong_question(
                question_id=question_id,
                question=resolved["question"],
                student_answer=student_answer,
                correct_answer=resolved["correct_answer"] or resolved["reference_answer"],
                analysis=result.get("analysis", ""),
                difficulty=difficulty,
                model_used=model_used,
                knowledge_point=resolved["knowledge_point"],
                subject=resolved["subject"],
                question_type=resolved["submit_type"],
            )

        result["model_used"] = model_used
        result["question_id"] = question_id
        return result

    async def explain_topic(self, topic: str, subject: str = "") -> Dict:
        logger.info(f"[讲解] 知识点={topic} 学科={subject}")

        search_result = retriever.search(topic, top_k=3)
        context = retriever.format_context(search_result)
        ai_response = await ai_service.call(
            prompt_name="explain",
            difficulty="normal",
            topic=topic,
            subject=subject or "未知学科",
            knowledge_context=context,
        )

        return {
            "topic": topic,
            "subject": subject,
            "explanation": ai_response,
            "knowledge_context": context[:300] + "..." if len(context) > 300 else context,
        }

    async def _generate_question_payload(
        self,
        difficulty: str,
        knowledge_point: str,
        subject: str,
        count: int,
        context: str,
    ) -> str:
        prompt_kwargs = {
            "knowledge_context": context,
            "knowledge_point": knowledge_point,
            "subject": subject or "未知学科",
            "count": str(count),
        }

        last_error = ""
        for attempt in range(2):
            if attempt == 1:
                logger.warning(f"[出题] 首次结构化输出失败，准备重试: {last_error[:120]}")
            ai_response = await ai_service.call(
                prompt_name="general",
                difficulty=difficulty,
                response_format={"type": "json_object"},
                output_schema_version="question-schema-v1",
                **prompt_kwargs,
            )
            parsed = self._load_question_json(ai_response)
            if parsed is not None and len(parsed.questions) == count:
                return ai_response
            last_error = "模型返回的题目 JSON 结构不合法或数量不匹配"
        raise ValueError(last_error or "模型未返回合法题目 JSON")

    def _parse_questions(
        self,
        ai_text: str,
        difficulty: str,
        count: int,
        knowledge_point: str,
        subject: str = "",
    ) -> List[Dict]:
        parsed = self._load_question_json(ai_text)
        if parsed is None:
            raise ValueError("模型未返回合法 JSON 题目结构")
        if len(parsed.questions) != count:
            raise ValueError(f"题目数量不匹配：期望 {count}，实际 {len(parsed.questions)}")

        questions: List[Dict] = []
        for item in parsed.questions:
            question_id = f"q_{uuid.uuid4().hex[:8]}"
            question_session_service.save_question(
                question_id=question_id,
                question_text=item.question_text,
                question_type=item.type,
                difficulty=difficulty,
                answer=item.answer,
                reference_answer=item.reference_answer,
                explanation=item.explanation,
                knowledge_point=knowledge_point,
                subject=subject,
            )
            questions.append(
                {
                    "id": question_id,
                    "question_text": item.question_text,
                    "type": item.type,
                    "difficulty": difficulty,
                    "options": item.options,
                }
            )
        return questions

    def _load_question_json(self, ai_text: str) -> Optional[GeneratedQuestionSet]:
        for candidate in self._extract_json_candidates(ai_text):
            try:
                return GeneratedQuestionSet.model_validate(json.loads(candidate))
            except Exception:
                continue
        return None

    def _extract_json_candidates(self, ai_text: str) -> List[str]:
        stripped = ai_text.strip()
        candidates = [stripped]
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1])
        unique_candidates = []
        for candidate in candidates:
            if candidate and candidate not in unique_candidates:
                unique_candidates.append(candidate)
        return unique_candidates

    def _resolve_question_payload(
        self,
        session,
        fallback_question: str,
        fallback_type: str,
        fallback_correct_answer: str,
        fallback_reference_answer: str,
        fallback_knowledge_point: str,
        fallback_subject: str,
    ) -> Dict:
        if session is None:
            return {
                "question": fallback_question,
                "submit_type": fallback_type,
                "correct_answer": fallback_correct_answer,
                "reference_answer": fallback_reference_answer,
                "knowledge_point": fallback_knowledge_point,
                "subject": fallback_subject,
            }
        return {
            "question": session.question_text,
            "submit_type": self._resolve_submit_type(session.question_type),
            "correct_answer": session.answer,
            "reference_answer": session.reference_answer or session.answer,
            "knowledge_point": session.knowledge_point or fallback_knowledge_point,
            "subject": session.subject or fallback_subject,
        }

    def _resolve_submit_type(self, question_type: str) -> str:
        if question_type in ("single_choice", "multiple_choice", "judge"):
            return "objective"
        return "advanced"

    def _parse_grading(self, ai_text: str, question_type: str) -> Dict:
        lines = ai_text.strip().split("\n")
        first_line = lines[0] if lines else ""

        if "正确" in first_line or "对" in first_line:
            conclusion = "正确"
        elif "错误" in first_line or "错" in first_line:
            conclusion = "错误"
        else:
            conclusion = "待定"

        return {
            "score": 100 if conclusion == "正确" else 0 if question_type == "objective" else 50,
            "conclusion": conclusion,
            "analysis": ai_text,
        }


exam_service = ExamService()
