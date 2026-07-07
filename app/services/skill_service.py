import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from app.config import settings
from app.services.ai_service import ai_service
from app.utils.logger import (
    get_recent_wrong_questions,
    get_stats,
    logger,
    should_trigger_optimization,
)


SKILL_DIR = Path(settings.SKILL_DIR)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = PROJECT_ROOT / "tests"

SKILL_MAP = {
    "scoring": "exam_skills/scoring.py",
    "chunking": "vector_skills/chunk_strategy.py",
    "api_call": "api_skills/ai_caller.py",
}


class SkillService:
    async def check_and_optimize(self) -> Optional[Dict]:
        if not should_trigger_optimization():
            return None

        logger.info("[Skill迭代] 达到阈值，开始分析可优化 Skill")
        wrong_questions = get_recent_wrong_questions(limit=20)
        stats = get_stats()
        skill_key = self._determine_skill_to_optimize(wrong_questions, stats)

        if not skill_key:
            return {"success": False, "message": "未找到可优化的 Skill"}

        return await self._optimize_skill(skill_key, wrong_questions, stats)

    def _determine_skill_to_optimize(self, wrong_questions: list, stats: dict) -> Optional[str]:
        if stats.get("api_errors", 0) > stats.get("wrong_questions", 0):
            return "api_call"
        if stats.get("wrong_questions", 0) > 0:
            return "scoring"
        return None

    async def _optimize_skill(self, skill_key: str, wrong_questions: list, stats: dict) -> Dict:
        file_path = SKILL_DIR / SKILL_MAP[skill_key]
        if not self._is_path_allowed(file_path):
            return {"success": False, "error": f"不允许修改白名单外路径: {file_path}"}
        if not file_path.exists():
            return {"success": False, "error": f"目标 Skill 文件不存在: {file_path}"}

        original_code = file_path.read_text(encoding="utf-8")
        wrong_data = json.dumps(
            [
                {
                    "question": item.get("question", ""),
                    "student_answer": item.get("student_answer", ""),
                    "correct_answer": item.get("correct_answer", ""),
                }
                for item in wrong_questions[-5:]
            ],
            ensure_ascii=False,
        )
        error_log = f"错题总数={stats['wrong_questions']}，API 异常={stats['api_errors']}"

        try:
            optimized_code = await ai_service.call(
                prompt_name="skill_optimize",
                difficulty="expert",
                skill_code=original_code,
                error_log=error_log,
                wrong_question_data=wrong_data,
            )
        except Exception as error:
            logger.error(f"[Skill迭代] AI 优化调用失败: {error}")
            return {"success": False, "error": f"AI 优化调用失败: {error}"}

        backup_path = file_path.with_suffix(".py.bak")
        candidate_path = file_path.with_name(file_path.stem + ".candidate.py")
        shutil.copy2(file_path, backup_path)

        try:
            candidate_path.write_text(optimized_code, encoding="utf-8")
            validation = self._validate_candidate(skill_key, candidate_path)
            if not validation["success"]:
                backup_path.unlink(missing_ok=True)
                return validation

            os.replace(candidate_path, file_path)
            backup_path.unlink(missing_ok=True)
            logger.info(f"[Skill迭代] 优化成功: {skill_key}")
            return {
                "success": True,
                "skill": skill_key,
                "message": "候选代码已通过语法检查、专项测试和核心回归测试",
                "file": str(file_path),
            }
        except Exception as error:
            if candidate_path.exists():
                candidate_path.unlink(missing_ok=True)
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                backup_path.unlink(missing_ok=True)
            logger.error(f"[Skill迭代] 候选代码验证失败: {error}")
            return {"success": False, "error": str(error)}

    def _validate_candidate(self, skill_key: str, candidate_path: Path) -> Dict:
        try:
            py_compile.compile(str(candidate_path), doraise=True)
        except py_compile.PyCompileError as error:
            candidate_path.unlink(missing_ok=True)
            return {"success": False, "error": f"候选文件语法检查失败: {error.msg}"}

        skill_test = TEST_DIR / f"test_{skill_key}.py"
        if not skill_test.exists():
            candidate_path.unlink(missing_ok=True)
            return {"success": False, "error": f"缺少专项测试文件: {skill_test.name}"}

        skill_result = self._run_python_test(skill_test, timeout=30)
        if not skill_result["success"]:
            candidate_path.unlink(missing_ok=True)
            return {"success": False, "error": f"专项测试失败: {skill_result['error']}"}

        core_test = TEST_DIR / "test_core.py"
        if core_test.exists():
            core_result = self._run_python_test(core_test, timeout=45)
            if not core_result["success"]:
                candidate_path.unlink(missing_ok=True)
                return {"success": False, "error": f"核心回归失败: {core_result['error']}"}

        return {"success": True}

    def _run_python_test(self, test_file: Path, timeout: int) -> Dict:
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode == 0:
                return {"success": True}
            error = (result.stderr or result.stdout or "未知错误").strip()
            return {"success": False, "error": error[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"测试超时(>{timeout}s)"}
        except Exception as error:
            return {"success": False, "error": str(error)}

    def _is_path_allowed(self, file_path: Path) -> bool:
        resolved = str(file_path.resolve())
        for allowed in settings.SKILL_WHITELIST:
            if allowed in resolved:
                return True
        return False


skill_service = SkillService()
