"""
============================================
 提示词加载器
============================================
【作用】
启动时将 prompts/ 目录下所有 .txt 文件加载到内存中，
运行时通过 get_prompt() 函数获取并填充动态占位符。

【为什么这么做？】
1. 性能：从内存读取比从硬盘读取快得多
2. 安全：启动加载后禁止修改，符合硬性约束
3. 简洁：调用方只需要说"我要 general 提示词"即可

【数据流】
  启动时 → loader.load_prompts() 扫描目录 → 存入内存字典
  运行时 → get_prompt("general", question="xxx") → 填充占位符 → 返回完整文本
"""

import os
import re
from pathlib import Path
from typing import Dict


# 【全局变量】存储所有提示词
# 字典结构：{"文件名（不含扩展名）": "文件文本内容"}
_prompts: Dict[str, str] = {}


def load_prompts(prompt_dir: str = None) -> Dict[str, str]:
    """
    【加载提示词】— 项目启动时调用一次
    
    参数:
        prompt_dir: 提示词目录路径，默认是当前文件所在目录下的 prompts/
    
    返回:
        提示词字典 {名称: 内容}
    
    原理:
        - 扫描目录下所有 .txt 文件
        - 文件名去掉 .txt 作为 key（如 "general.txt" → "general"）
        - 文件全部内容作为 value
    """
    global _prompts
    
    # 如果没有指定目录，就用当前文件上一级目录（app/prompts/）
    if prompt_dir is None:
        prompt_dir = os.path.join(os.path.dirname(__file__))
    
    # 清空旧数据（防止重复加载）
    _prompts.clear()
    
    # 扫描所有 .txt 文件
    prompt_path = Path(prompt_dir)
    for txt_file in prompt_path.glob("*.txt"):
        # 文件名（不含扩展名）作为键名
        name = txt_file.stem  # "general.txt" -> "general"
        
        # 读取文件全部内容
        content = txt_file.read_text(encoding="utf-8")
        
        # 存入内存字典
        _prompts[name] = content
    
    return _prompts


def get_prompt(name: str, **kwargs) -> str:
    """
    【获取提示词】— 运行时调用
    
    参数:
        name: 提示词名称（对应文件名，不含 .txt）
        **kwargs: 要替换的占位符（如 question="1+1=?"）
    
    返回:
        替换完占位符后的完整提示词文本
    
    使用示例:
        prompt = get_prompt("general", question="什么是戴维南定理？")
    
    原理:
        - 从内存字典中取出对应提示词文本
        - 用传入的参数替换文本中的 {{占位符}}
        - 简单字符串替换，用 Python 的 replace()
          （更安全的做法是用正则匹配 {{...}}）
    """
    # 从内存字典获取提示词原文
    raw = _prompts.get(name)
    if raw is None:
        raise ValueError(f"提示词 '{name}' 未找到，可用提示词: {list(_prompts.keys())}")
    
    # 替换所有 {{占位符}} 为传入的实际值
    result = raw
    for key, value in kwargs.items():
        # {{key}} 格式的占位符
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    
    return result


def list_prompts() -> list:
    """返回所有可用的提示词名称列表"""
    return list(_prompts.keys())


def get_prompt_count() -> int:
    """返回已加载的提示词数量"""
    return len(_prompts)
