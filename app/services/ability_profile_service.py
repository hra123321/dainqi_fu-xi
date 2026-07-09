"""基于错题记录生成能力画像。"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.utils.logger import WRONG_QUESTIONS_FILE


ERROR_TYPES = {
    "concept": ("概念", "定义", "原理", "理解"),
    "formula": ("公式", "代入", "符号", "单位", "角标"),
    "calculation": ("计算", "算错", "结果", "数值"),
    "reading": ("审题", "题意", "条件", "遗漏"),
    "operation": ("步骤", "操作", "配置", "组态", "软件"),
}


class AbilityProfileService:
    """把错题列表整理为领域、知识点和错误类型画像。"""

    def __init__(self, wrong_questions_file: str | Path | None = None) -> None:
        self.wrong_questions_file = Path(wrong_questions_file or WRONG_QUESTIONS_FILE)

    def build_profile(self) -> dict[str, Any]:
        questions = self._load_questions()
        by_subject: dict[str, dict[str, Any]] = {}
        node_counter = Counter()
        error_counter = Counter()
        difficulty_counter = Counter()

        grouped = defaultdict(list)
        for item in questions:
            subject = item.get("subject") or "未知学科"
            topic = item.get("knowledge_point") or "未知知识点"
            grouped[(subject, topic)].append(item)
            node_counter[(subject, topic)] += 1
            error_type = self._classify_error(item)
            error_counter[error_type] += 1
            difficulty_counter[item.get("difficulty") or "normal"] += 1

        for (subject, topic), items in grouped.items():
            subject_entry = by_subject.setdefault(
                subject,
                {
                    "subject": subject,
                    "wrongCount": 0,
                    "weakNodes": [],
                    "errorTypes": Counter(),
                },
            )
            subject_entry["wrongCount"] += len(items)
            local_errors = Counter(self._classify_error(item) for item in items)
            subject_entry["errorTypes"].update(local_errors)
            subject_entry["weakNodes"].append(
                {
                    "knowledgePoint": topic,
                    "wrongCount": len(items),
                    "mainErrorType": local_errors.most_common(1)[0][0],
                    "reviewPriority": self._priority(len(items), items),
                }
            )

        subjects = []
        for subject_entry in by_subject.values():
            subject_entry["errorTypes"] = dict(subject_entry["errorTypes"])
            subject_entry["weakNodes"].sort(key=lambda item: item["reviewPriority"], reverse=True)
            subjects.append(subject_entry)
        subjects.sort(key=lambda item: item["wrongCount"], reverse=True)

        weakest = [
            {
                "subject": subject,
                "knowledgePoint": topic,
                "wrongCount": count,
            }
            for (subject, topic), count in node_counter.most_common(10)
        ]

        return {
            "totalWrong": len(questions),
            "subjects": subjects,
            "weakestNodes": weakest,
            "errorTypeDistribution": dict(error_counter),
            "difficultyDistribution": dict(difficulty_counter),
            "recommendations": self._recommend(weakest),
        }

    def _load_questions(self) -> list[dict[str, Any]]:
        if not self.wrong_questions_file.exists():
            return []
        questions = []
        with self.wrong_questions_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    questions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return questions

    def _classify_error(self, item: dict[str, Any]) -> str:
        text = " ".join(
            str(item.get(key, ""))
            for key in ("analysis", "question", "student_answer", "correct_answer", "question_type")
        )
        for error_type, markers in ERROR_TYPES.items():
            if any(marker in text for marker in markers):
                return error_type
        return "unknown"

    def _priority(self, wrong_count: int, items: list[dict[str, Any]]) -> int:
        difficulty_weight = {"easy": 1, "normal": 2, "hard": 3, "expert": 4}
        max_difficulty = max(difficulty_weight.get(item.get("difficulty", "normal"), 2) for item in items)
        return wrong_count * 10 + max_difficulty

    def _recommend(self, weakest: list[dict[str, Any]]) -> list[dict[str, str]]:
        recommendations = []
        for item in weakest[:5]:
            action = "优先复习该知识点并生成同类变式题" if item["wrongCount"] >= 3 else "安排一次针对性回顾"
            recommendations.append(
                {
                    "subject": item["subject"],
                    "knowledgePoint": item["knowledgePoint"],
                    "action": action,
                }
            )
        return recommendations


ability_profile_service = AbilityProfileService()
