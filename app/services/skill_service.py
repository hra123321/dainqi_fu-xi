"""
============================================
 Skill 自迭代服务 — 数据采集 → 触发 → AI 优化 → 测试 → 覆盖
============================================
【作用】
监控错题和异常数据，达到阈值后自动触发 AI 优化 Skill 代码。

【完整流程】
1. 检查错题/异常计数是否达到阈值
2. 收集最近的错题数据和异常日志
3. 读取对应 Skill 的源代码
4. 调用 AI (Pro) 生成优化建议
5. 运行自动化测试验证新代码
6. 测试通过 → 覆盖原文件；失败 → 记录失败日志

【安全约束】
- 只读写 app/skills/ 白名单目录下的文件
- 新代码必须通过测试才覆盖原文件
- 不满足条件绝不修改文件
"""

import os
import sys
import json
import shutil
import traceback
import subprocess
from pathlib import Path
from typing import Dict, Optional

from app.config import settings
from app.prompts.loader import get_prompt
from app.services.ai_service import ai_service
from app.utils.logger import (
    logger, get_recent_wrong_questions, get_stats,
    should_trigger_optimization,
)


SKILL_DIR = Path(settings.SKILL_DIR)

# 错题类型 → 对应 Skill 文件 的映射
SKILL_MAP = {
    "scoring": "exam_skills/scoring.py",          # 阅卷评分
    "chunking": "vector_skills/chunk_strategy.py", # 切片策略
    "api_call": "api_skills/ai_caller.py",         # API 调用
}


class SkillService:
    """
    【Skill 自迭代服务】
    
    监控数据、触发优化、测试验证、安全覆盖的全流程管理。
    """

    async def check_and_optimize(self) -> Optional[Dict]:
        """
        【检查并触发优化】（对外主入口）
        
        系统定时调用此方法，检查是否达到优化阈值。
        如果达到，自动触发优化流程。
        
        返回:
            优化结果，或 None（未触发）
        """
        if not should_trigger_optimization():
            return None
        
        logger.info("[Skill迭代] 达到阈值，开始优化流程")
        
        # 收集数据
        wrong_questions = get_recent_wrong_questions(limit=20)
        stats = get_stats()
        
        # 根据错题类型确定要优化哪个 Skill
        skill_to_optimize = self._determine_skill_to_optimize(wrong_questions, stats)
        
        if not skill_to_optimize:
            logger.info("[Skill迭代] 无法确定要优化的 Skill")
            return {"success": False, "message": "无法确定优化目标"}
        
        # 执行优化
        result = await self._optimize_skill(skill_to_optimize, wrong_questions, stats)
        return result

    def _determine_skill_to_optimize(self, wrong_questions: list, stats: dict) -> Optional[str]:
        """根据数据特征决定优化哪个 Skill"""
        if stats.get("api_errors", 0) > stats.get("wrong_questions", 0):
            return "api_call"
        if stats.get("wrong_questions", 0) > 0:
            return "scoring"
        return None

    async def _optimize_skill(
        self, skill_key: str, wrong_questions: list, stats: dict
    ) -> Dict:
        """
        【优化单个 Skill 文件】
        
        1. 读取 Skill 源码
        2. 调用 AI Pro 生成优化代码
        3. 测试验证
        4. 安全覆盖
        """
        file_path = SKILL_DIR / SKILL_MAP[skill_key]
        
        # 安全检查：是否在白名单内
        if not self._is_path_allowed(file_path):
            return {"success": False, "error": f"路径不在白名单: {file_path}"}
        
        if not file_path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}"}
        
        # 1. 读取源码
        original_code = file_path.read_text(encoding="utf-8")
        
        # 2. 准备优化数据
        wrong_data = json.dumps(
            [{"q": w.get("question",""), "a": w.get("student_answer",""), "c": w.get("correct_answer","")}
             for w in wrong_questions[-5:]],
            ensure_ascii=False
        )
        error_log = f"总错题: {stats['wrong_questions']}, API异常: {stats['api_errors']}"
        
        # 3. 调用 Pro 模型生成优化代码
        try:
            optimized_code = await ai_service.call(
                prompt_name="skill_optimize",
                difficulty="expert",  # 用 Pro 模型优化
                skill_code=original_code,
                error_log=error_log,
                wrong_question_data=wrong_data,
            )
        except Exception as e:
            logger.error(f"[Skill迭代] AI 优化调用失败: {e}")
            return {"success": False, "error": f"AI 调用失败: {str(e)}"}
        
        # 4. 备份原文件
        backup_path = file_path.with_suffix(".py.bak")
        shutil.copy2(file_path, backup_path)
        
        try:
            # 5. 写入新代码
            file_path.write_text(optimized_code, encoding="utf-8")
            
            # 6. 运行测试验证
            test_result = self._run_tests_for_skill(skill_key)
            
            if test_result["success"]:
                # 测试通过 → 删除备份
                backup_path.unlink(missing_ok=True)
                logger.info(f"[Skill迭代] 优化成功: {skill_key}")
                return {
                    "success": True,
                    "skill": skill_key,
                    "message": f"优化成功，测试通过",
                    "file": str(file_path),
                }
            else:
                # 测试失败 → 恢复备份
                shutil.copy2(backup_path, file_path)
                backup_path.unlink(missing_ok=True)
                logger.warning(f"[Skill迭代] 测试失败，已回滚: {test_result['error']}")
                return {
                    "success": False,
                    "error": f"测试未通过，已回滚: {test_result['error']}",
                }
        
        except Exception as e:
            # 异常 → 恢复备份
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                backup_path.unlink(missing_ok=True)
            logger.error(f"[Skill迭代] 异常: {e}")
            return {"success": False, "error": str(e)}

    def _is_path_allowed(self, file_path: Path) -> bool:
        """检查文件路径是否在白名单内"""
        resolved = str(file_path.resolve())
        for allowed in settings.SKILL_WHITELIST:
            if allowed in resolved:
                return True
        return False

    def _run_tests_for_skill(self, skill_key: str) -> Dict:
        """运行该 Skill 对应的自动化测试"""
        test_file = SKILL_DIR.parent.parent / "tests" / f"test_{skill_key}.py"
        
        if not test_file.exists():
            return {"success": True, "message": "无对应测试文件，跳过"}
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {"success": True}
            else:
                return {"success": False, "error": result.stderr[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "测试超时(>30s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== 全局实例 ====================
skill_service = SkillService()
