import json

from app.services.skill_service import skill_service
from app.services.ability_profile_service import ability_profile_service
from app.utils.logger import WRONG_QUESTIONS_FILE, get_stats, get_weakest_topics, logger


class WrongBookService:
    def get_all_wrong_questions(
        self,
        limit=100,
        offset=0,
        difficulty=None,
        knowledge_point=None,
        sort_by="newest",
    ):
        if not WRONG_QUESTIONS_FILE.exists():
            return {"questions": [], "total": 0}

        questions = []
        with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if difficulty and item.get("difficulty") != difficulty:
                        continue
                    if knowledge_point and knowledge_point not in item.get("knowledge_point", ""):
                        continue
                    questions.append(item)
                except json.JSONDecodeError:
                    continue

        if sort_by == "newest":
            questions.reverse()

        total = len(questions)
        return {"questions": questions[offset: offset + limit], "total": total}

    def get_analysis(self):
        stats = get_stats()
        weakest_topics = get_weakest_topics(5)
        difficulty_distribution = {"easy": 0, "normal": 0, "hard": 0, "expert": 0}

        if WRONG_QUESTIONS_FILE.exists():
            with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as file:
                for line in file:
                    try:
                        item = json.loads(line)
                        difficulty = item.get("difficulty", "normal")
                        if difficulty in difficulty_distribution:
                            difficulty_distribution[difficulty] += 1
                    except json.JSONDecodeError:
                        continue

        review_suggestions = []
        for topic in weakest_topics:
            action = "建议优先复习并重新做题" if topic["count"] >= 3 else "建议安排一次回顾"
            review_suggestions.append({
                "topic": topic["topic"],
                "wrong_count": topic["count"],
                "action": action,
            })

        return {
            "total_wrong": stats["wrong_questions"],
            "weakest_topics": weakest_topics,
            "difficulty_distribution": difficulty_distribution,
            "review_suggestions": review_suggestions,
            "should_optimize": stats["should_optimize"],
        }

    def get_ability_profile(self):
        return ability_profile_service.build_profile()

    async def auto_evolve(self):
        logger.info("[自进化] 开始分析错题模式")
        weakest_topics = get_weakest_topics(3)
        if not weakest_topics:
            return {"message": "暂无错题数据"}

        stats = get_stats()
        optimization_result = None
        if stats["should_optimize"]:
            logger.info("[自进化] 达到阈值，触发 Skill 优化")
            optimization_result = await skill_service.check_and_optimize()

        return {
            "weakest_topics": weakest_topics,
            "optimization_result": optimization_result,
            "message": "自进化分析完成",
        }

    def clear_wrong_questions(self):
        try:
            if WRONG_QUESTIONS_FILE.exists():
                WRONG_QUESTIONS_FILE.unlink()
            return True
        except Exception:
            return False


wrong_book_service = WrongBookService()
