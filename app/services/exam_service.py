"""
============================================
 刷题业务服务 — 业务逻辑编排
============================================
【作用】
组合 AI 调用、知识检索、错题记录等功能，
完成"出题→作答→批改"的业务闭环。

【不做什么？】
- 不直接调 DeepSeek API（交给 ai_service）
- 不直接操作 Chroma（交给 retriever）
- 不处理 HTTP 请求（交给 router）
"""

import uuid
from typing import List, Dict

from app.services.ai_service import ai_service
from app.vector_db.retriever import retriever
from app.models.dispatch import get_model_for_difficulty
from app.utils.logger import (
    logger, record_wrong_question, get_wrong_question_count,
    get_error_count, should_trigger_optimization,
)


class ExamService:
    """
    【考试服务】
    
    刷题业务的核心编排者。
    """

    async def generate_questions(
        self,
        knowledge_point: str,
        difficulty: str = "normal",
        count: int = 5,
    ) -> Dict:
        """
        【出题】
        
        根据知识点和难度，让 AI 生成题目。
        
        参数:
            knowledge_point: 知识点名称
            difficulty: 难度标签
            count: 出题数量
        
        返回:
            {
                "questions": [...],        # 题目列表
                "knowledge_context": "...", # 用的参考内容
                "model_used": "..."        # 用了 Flash 还是 Pro
            }
        """
        logger.info(f"[出题] 知识点={knowledge_point} 难度={difficulty} 数量={count}")
        
        # 1. 检索知识库，获取相关参考内容
        search_result = retriever.search(knowledge_point, top_k=5)
        context = retriever.format_context(search_result)
        
        # 2. 确定用哪个模型
        model_used = get_model_for_difficulty(difficulty)
        
        # 3. 调用 AI 出题
        prompt_kwargs = {
            "knowledge_context": context,
            "knowledge_point": knowledge_point,
            "count": str(count),
        }
        
        ai_response = await ai_service.call(
            prompt_name="general",
            difficulty=difficulty,
            **prompt_kwargs,
        )
        
        # 4. 解析 AI 返回的题目
        # 先把 AI 返回的整段文字按题目分割
        questions = self._parse_questions(ai_response, difficulty)
        
        return {
            "questions": questions,
            "knowledge_context": context[:500] + "...",  # 只返回摘要
            "model_used": model_used,
        }

    async def grade_answer(
        self,
        question_id: str,
        question: str,
        question_type: str,
        student_answer: str,
        correct_answer: str = None,
        reference_answer: str = None,
        knowledge_context: str = "",
    ) -> Dict:
        """
        【批改答案】
        
        批改学生提交的答案，返回评分和解析。
        
        参数:
            question_id: 题目 ID
            question: 题目原文
            question_type: objective(客观题) / advanced(高阶题)
            student_answer: 学生答案
            correct_answer: 标准答案（客观题用）
            reference_answer: 参考答案（高阶题用）
            knowledge_context: 知识点参考
        
        返回:
            {
                "score": 100,
                "conclusion": "正确/错误",
                "analysis": "详细解析...",
                "model_used": "..."
            }
        """
        logger.info(f"[批改] {question_id} | 题型={question_type}")
        
        # 根据题型选择提示词和难度
        if question_type == "objective":
            # 客观题（选择/判断）— 用 Flash 快速批改
            prompt_name = "objective_mcq"
            difficulty = "easy"
            prompt_kwargs = {
                "question": question,
                "correct_answer": correct_answer or "",
                "student_answer": student_answer,
                "knowledge_context": knowledge_context,
            }
        else:
            # 高阶题（计算/推导）— 用 Pro 深度批改
            prompt_name = "advanced_answer"
            difficulty = "hard"
            prompt_kwargs = {
                "question": question,
                "reference_answer": reference_answer or "",
                "student_answer": student_answer,
                "knowledge_context": knowledge_context,
            }
        
        # 调用 AI 批改
        ai_response = await ai_service.call(
            prompt_name=prompt_name,
            difficulty=difficulty,
            **prompt_kwargs,
        )
        
        # 解析批改结果
        model_used = get_model_for_difficulty(difficulty)
        result = self._parse_grading(ai_response, question_type)
        
        # 记录错题（如果答错了）
        is_correct = result.get("conclusion", "").strip() == "正确"
        if not is_correct:
            record_wrong_question(
                question_id=question_id,
                question=question,
                student_answer=student_answer,
                correct_answer=correct_answer or reference_answer or "",
                analysis=result.get("analysis", ""),
                difficulty=difficulty,
                model_used=model_used,
            )
        
        result["model_used"] = model_used
        return result

    def _parse_questions(self, ai_text: str, difficulty: str) -> List[Dict]:
        """
        【解析 AI 生成的题目】
        
        把 AI 返回的一大段文字解析成结构化的题目列表。
        这里用简单的按空行分割，后续可以改进为更智能的解析。
        """
        questions = []
        # 按两个换行分割成段落
        paragraphs = [p.strip() for p in ai_text.split("\n\n") if p.strip()]
        
        for i, para in enumerate(paragraphs):
            questions.append({
                "id": f"q_{uuid.uuid4().hex[:8]}",
                "question_text": para,
                "type": "analyze" if difficulty in ("hard", "expert") else "choice",
                "difficulty": difficulty,
            })
        
        # 确保不超过请求数量
        return questions[:5]

    def _parse_grading(self, ai_text: str, question_type: str) -> Dict:
        """
        【解析 AI 批改结果】
        
        从 AI 返回的文本中提取评分信息。
        简单实现：直接返回原始文本，前端自行渲染。
        """
        # 提取结论（第一行）
        lines = ai_text.strip().split("\n")
        first_line = lines[0] if lines else ""
        
        # 判断是否正确
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


# ==================== 全局实例 ====================
exam_service = ExamService()
