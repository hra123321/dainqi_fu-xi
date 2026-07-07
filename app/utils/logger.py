"""
============================================
 日志系统 — 运行日志 + 错题采集 + 异常记录
============================================
【作用】
1. 记录系统运行日志（谁在什么时候调用了什么）
2. 采集错题数据（为 Skill 自迭代提供素材）
3. 记录程序异常（触发 AI 优化的重要信号）
4. 判断是否达到自动优化阈值

【数据流向】
  学生做题 → 批改结果 → 错题记录 → 累计计数
                                     ↓
  达到阈值(10条) → 触发 Skill 优化 → AI 改进代码
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ==================== 日志路径 ====================
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 错题数据文件
WRONG_QUESTIONS_FILE = LOG_DIR / "wrong_questions.jsonl"
# 异常记录文件
ERROR_LOG_FILE = LOG_DIR / "errors.jsonl"


# ==================== 配置 Python 标准日志 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(),  # 同时在控制台输出
    ],
)
logger = logging.getLogger("exam_system")


# ==================== 错题采集 ====================

def record_wrong_question(
    question_id: str,
    question: str,
    student_answer: str,
    correct_answer: str,
    analysis: str,
    difficulty: str,
    model_used: str,
    knowledge_point: str = "",
    subject: str = "",
    question_type: str = "",
):
    """
    【记录错题】
    
    当学生答错题时，记录这道题的完整信息。
    这些数据会触发 AI 优化 Skill 代码。
    
    每条错题是 JSONL 格式的一行（每行一个 JSON 对象）。
    JSONL 比 CSV 好：每行独立，方便追加和读取。
    """
    record = {
        "timestamp": datetime.now().isoformat(),
        "question_id": question_id,
        "question": question,
        "student_answer": student_answer,
        "correct_answer": correct_answer,
        "analysis": analysis,
        "difficulty": difficulty,
        "model_used": model_used,
        "knowledge_point": knowledge_point,
        "subject": subject,
        "question_type": question_type,
    }
    
    # 追加写入（a = append 追加模式）
    with open(WRONG_QUESTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    logger.info(f"错题记录: {question_id} | {difficulty} | {model_used}")


def record_api_error(
    api_name: str,
    model: str,
    error_message: str,
    prompt_name: str = "",
):
    """
    【记录 API 异常】
    
    当 AI 调用失败时记录，用于触发 Skill 优化。
    """
    record = {
        "timestamp": datetime.now().isoformat(),
        "api_name": api_name,
        "model": model,
        "error": error_message,
        "prompt_name": prompt_name,
    }
    
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    logger.error(f"API 异常: {api_name} | {model} | {error_message[:100]}")


# ==================== 统计数据查询 ====================

def get_wrong_question_count() -> int:
    """获取错题总数"""
    if not WRONG_QUESTIONS_FILE.exists():
        return 0
    count = 0
    with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def get_error_count() -> int:
    """获取异常总数"""
    if not ERROR_LOG_FILE.exists():
        return 0
    count = 0
    with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def get_recent_wrong_questions(limit: int = 20) -> List[Dict]:
    """
    【获取最近的错题】
    
    返回最近的错题数据，用于 AI 优化时分析。
    limit 参数控制返回条数，避免一次传太多数据给 AI。
    """
    if not WRONG_QUESTIONS_FILE.exists():
        return []
    
    questions = []
    with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    
    # 返回最新的（文件末尾的）limit 条
    return questions[-limit:]


def should_trigger_optimization() -> bool:
    """
    【判断是否达到优化阈值】
    
    根据错题数和异常数判断是否触发 Skill 自迭代。
    
    返回:
        True = 需要触发优化
        False = 还不到时候
    """
    from app.config import settings
    threshold = settings.AUTO_OPTIMIZE_THRESHOLD
    
    wrong_count = get_wrong_question_count()
    error_count = get_error_count()
    total = wrong_count + error_count
    
    trigger = total >= threshold
    if trigger:
        logger.info(
            f"达到优化阈值: 错题{wrong_count}+异常{error_count}"
            f"={total} >= {threshold}，准备触发 AI 优化"
        )
    
    return trigger



def get_wrong_questions_by_knowledge_point() -> dict:
    """按知识点统计错题数量"""
    if not WRONG_QUESTIONS_FILE.exists():
        return {}
    stats = {}
    with open(WRONG_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                q = json.loads(line)
                kp = q.get("knowledge_point", "未知")
                if kp not in stats:
                    stats[kp] = {"count": 0, "questions": []}
                stats[kp]["count"] += 1
                stats[kp]["questions"].append(q)
            except json.JSONDecodeError:
                continue
    return stats


def get_weakest_topics(top_n: int = 5) -> list:
    """获取错题最多的知识点排行"""
    stats = get_wrong_questions_by_knowledge_point()
    sorted_topics = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)
    return [{"topic": k, "count": v["count"]} for k, v in sorted_topics[:top_n]]


def get_stats() -> Dict:
    """获取日志统计摘要"""
    return {
        "wrong_questions": get_wrong_question_count(),
        "api_errors": get_error_count(),
        "should_optimize": should_trigger_optimization(),
    }
