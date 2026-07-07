"""
题目会话服务
"""

import time
from dataclasses import dataclass
from typing import Dict, Optional

from app.config import settings


@dataclass
class QuestionSession:
    question_id: str
    question_text: str
    question_type: str
    difficulty: str
    answer: str
    reference_answer: str
    explanation: str
    knowledge_point: str
    subject: str
    created_at: float
    expire_at: float


class QuestionSessionService:
    """在服务端暂存题目答案，避免把答案下发到前端。"""

    def __init__(self, ttl_seconds: int = None):
        self._ttl_seconds = ttl_seconds or settings.QUESTION_SESSION_TTL
        self._sessions: Dict[str, QuestionSession] = {}

    def save_question(
        self,
        question_id: str,
        question_text: str,
        question_type: str,
        difficulty: str,
        answer: str,
        reference_answer: str,
        explanation: str,
        knowledge_point: str,
        subject: str = "",
    ) -> None:
        now = time.time()
        self._sessions[question_id] = QuestionSession(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            difficulty=difficulty,
            answer=answer,
            reference_answer=reference_answer,
            explanation=explanation,
            knowledge_point=knowledge_point,
            subject=subject,
            created_at=now,
            expire_at=now + self._ttl_seconds,
        )

    def get_question(self, question_id: str) -> Optional[QuestionSession]:
        session = self._sessions.get(question_id)
        if session is None:
            return None
        if time.time() > session.expire_at:
            del self._sessions[question_id]
            return None
        return session

    def delete_question(self, question_id: str) -> None:
        self._sessions.pop(question_id, None)

    def clear_expired(self) -> None:
        now = time.time()
        expired_ids = [question_id for question_id, session in self._sessions.items() if now > session.expire_at]
        for question_id in expired_ids:
            del self._sessions[question_id]

    @property
    def size(self) -> int:
        self.clear_expired()
        return len(self._sessions)


question_session_service = QuestionSessionService()
