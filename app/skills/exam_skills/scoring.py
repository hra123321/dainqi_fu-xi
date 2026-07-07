import re
from typing import Dict


def parse_grading_result(ai_text: str, question_type: str) -> Dict:
    score = 50
    conclusion = "待定"
    analysis = ai_text or ""

    first_line = analysis.strip().split("\n")[0] if analysis else ""
    if "正确" in first_line or "对" in first_line:
        conclusion = "正确"
        score = 100
    elif "错误" in first_line or "错" in first_line:
        conclusion = "错误"
        score = 0

    if question_type == "advanced":
        score_match = re.search(r"总分[：:]\s*(\d+)(?:\s*[分/])?", analysis)
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
    if not student_answer or not correct_answer:
        return False
    return student_answer.strip().upper() == correct_answer.strip().upper()
