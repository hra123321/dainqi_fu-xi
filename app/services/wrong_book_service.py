import json
from collections import defaultdict
from app.utils.logger import WRONG_QUESTIONS_FILE, get_weakest_topics, get_stats
from app.services.skill_service import skill_service
from app.utils.logger import logger

class WrongBookService:

    def get_all_wrong_questions(self, limit=100, offset=0, difficulty=None, knowledge_point=None, sort_by="newest"):
        if not WRONG_QUESTIONS_FILE.exists():
            return {"questions": [], "total": 0}
        questions = []
        with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    q = json.loads(line)
                    if difficulty and q.get("difficulty") != difficulty: continue
                    if knowledge_point and knowledge_point not in q.get("knowledge_point", ""): continue
                    questions.append(q)
                except: continue
        if sort_by == "newest": questions.reverse()
        total = len(questions)
        return {"questions": questions[offset:offset+limit], "total": total}

    def get_analysis(self):
        stats = get_stats()
        weakest = get_weakest_topics(5)
        diff_dist = {"easy": 0, "normal": 0, "hard": 0, "expert": 0}
        if WRONG_QUESTIONS_FILE.exists():
            with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        q = json.loads(line)
                        d = q.get("difficulty", "normal")
                        if d in diff_dist: diff_dist[d] += 1
                    except: pass
        suggestions = []
        for t in weakest:
            suggestions.append({"topic": t["topic"], "wrong_count": t["count"],
                              "action": "需要立即复习" if t["count"] >= 3 else "建议复习"})
        return {
            "total_wrong": stats["wrong_questions"],
            "weakest_topics": weakest,
            "difficulty_distribution": diff_dist,
            "review_suggestions": suggestions,
            "should_optimize": stats["should_optimize"],
        }

    async def auto_evolve(self):
        logger.info("[自进化] 开始分析错题模式...")
        weakest = get_weakest_topics(3)
        if not weakest:
            return {"message": "暂无错题数据"}
        stats = get_stats()
        opt_result = None
        if stats["should_optimize"]:
            logger.info("[自进化] 触发 Skill 自迭代")
            opt_result = await skill_service.check_and_optimize()
        return {"weakest_topics": weakest, "optimization_result": opt_result, "message": "自进化完成"}

    def clear_wrong_questions(self):
        try:
            if WRONG_QUESTIONS_FILE.exists(): WRONG_QUESTIONS_FILE.unlink()
            return True
        except: return False

wrong_book_service = WrongBookService()