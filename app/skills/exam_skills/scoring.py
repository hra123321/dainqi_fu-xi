"""
============================================
 阅卷评分 Skill — 解析 AI 批改结果、计算得分
============================================
【作用】
解析 AI 返回的批改文本，提取分数和评语。
如果解析逻辑出错（拿不到分数），AI 可以优化这里。

【白名单】
本文件位于 app/skills/ 下，AI 可自动修改。
"""

import re
from typing import Dict


def parse_grading_result(ai_text: str, question_type: str) -> Dict:
    """
    【解析批改结果】
    
    从 AI 返回的文本中提取关键信息：结论、分数、解析。
    
    参数:
        ai_text: AI 返回的批改文本
        question_type: objective(客观题) / advanced(高阶题)
    
    返回:
        {"score": 100, "conclusion": "正确/错误", "analysis": "..."}
    """
    score = 50  # 默认分数
    conclusion = "待定"
    analysis = ai_text
    
    # 提取结论
    first_line = ai_text.strip().split("\n")[0] if ai_text else ""
    if "正确" in first_line or "对" in first_line:
        conclusion = "正确"
        score = 100
    elif "错误" in first_line or "错" in first_line:
        conclusion = "错误"
        score = 0
    
    # 高阶题尝试提取百分制分数
    if question_type == "advanced":
        score_match = re.search(r"总分[：:]\s*(\d+)(?:\s*[分/])?", ai_text)
        if score_match:
            parsed = int(score_match.group(1))
            if 0 <= parsed <= 100:
                score = parsed
    
    return {
        "score": score,
        "conclusion": conclusion,
        "analysis": analysis,
    }


def is_answer_correct(student_answer: str, correct_answer: str) -> bool:
    """
    【判断答案是否正确】（客观题备用方案）
    
    当 AI 调用失败时，用简单字符串匹配判断。
    """
    if not student_answer or not correct_answer:
        return False
    return student_answer.strip().upper() == correct_answer.strip().upper()
