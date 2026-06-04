"""
============================================
 模型分层调度器
============================================
【作用】
根据任务难度标签，自动选择调用 DeepSeek 的哪个模型。
规则固化在代码中，运行时不可修改（硬性约束）。

【难度分级】
- easy / normal → Flash（常规业务）
- hard / expert → Pro（高阶推理）

【为什么分层？】
1. 节省成本：简单任务用便宜模型，复杂任务用好模型
2. 提升速度：大部分请求走 Flash，响应更快
3. 保证质量：真正难的题才用 Pro，不浪费推理能力
"""

from app.config import settings


# ==================== 难度 → 模型映射表（固化规则） ====================
# 【关键数据结构】
# 字典（dict）是 Python 中"键→值"的映射表
# 键是难度标签，值是对应的模型名称
# 
# 规则固化说明：
# - 这个字典是模块级常量（全大写命名），运行期间不可修改
# - 如需新增难度等级，必须在这里明确指定使用哪个模型
_DIFFICULTY_MAP = {
    # 常规业务 → 使用 Flash（速度快）
    "easy": settings.MODEL_FLASH,      # 简单题：概念选择题、判断题
    "normal": settings.MODEL_FLASH,    # 普通题：一般计算题

    # 高阶推理 → 使用 Pro（能力强）
    "hard": settings.MODEL_PRO,        # 困难题：复杂电路分析、多步推导
    "expert": settings.MODEL_PRO,      # 专家级：综合应用题、开放性设计题
}


# 所有合法的难度标签集合（用于校验）
VALID_DIFFICULTIES = set(_DIFFICULTY_MAP.keys())


def get_model_for_difficulty(difficulty: str) -> str:
    """
    【根据难度获取模型】— 核心调度函数
    
    参数:
        difficulty: 难度标签，必须是 "easy"/"normal"/"hard"/"expert" 之一
    
    返回:
        模型名称字符串
    
    异常:
        ValueError: 如果传入不认识的难度标签
    
    使用示例:
        >>> get_model_for_difficulty("easy")
        'deepseek-chat'
        >>> get_model_for_difficulty("hard")
        'deepseek-reasoner'
    """
    if difficulty not in _DIFFICULTY_MAP:
        raise ValueError(
            f"不支持的难度标签: '{difficulty}'。"
            f"合法选项: {', '.join(VALID_DIFFICULTIES)}"
        )
    return _DIFFICULTY_MAP[difficulty]


def is_pro_model(difficulty: str) -> bool:
    """
    【判断是否使用 Pro 模型】
    
    用于日志记录、统计 Pro 模型使用频率等辅助功能
    
    参数:
        difficulty: 难度标签
    
    返回:
        True = 使用 Pro 模型（hard/expert）
        False = 使用 Flash 模型（easy/normal）
    """
    model = get_model_for_difficulty(difficulty)
    return model == settings.MODEL_PRO


def get_all_rules() -> dict:
    """
    【获取完整的调度规则】
    
    用于在管理页面展示当前的分流规则配置
    
    返回:
        包含所有难度→模型映射的字典
    """
    return dict(_DIFFICULTY_MAP)
