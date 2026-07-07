"""
============================================
 缓存键生成器（适配 DeepSeek 服务端缓存）
============================================
【作用】
生成标准化、确定性（每次相同输入→相同输出）的缓存键，
帮助 DeepSeek 服务端识别重复请求，提升缓存命中率。

【为什么需要这个？】
DeepSeek 的服务端缓存机制会检查请求内容是否相同。
如果两次请求的文本只有"多余空格"的差异，服务端会认为是不同请求。
所以我们先把文本"洗干净"，让相同含义的文本生成相同的缓存键。

【文本标准化处理流程】
1. 去除 BOM 头（\ufeff）
2. 统一 Unicode 规范化（NFKC）
3. 合并连续空白（多个空格/换行变成一个空格）
4. 去除首尾空白
5. 全部小写（选项字母等）
6. 生成 SHA256 哈希
"""

import hashlib
import unicodedata
import re


def normalize_text(text: str) -> str:
    """
    【文本标准化】— 核心清洗函数
    
    把用户输入的文本"洗干净"，去除无关格式差异。
    相同含义的不同格式 → 相同的标准化结果。
    
    参数:
        text: 原始输入文本
    
    返回:
        标准化后的文本字符串
    
    示例:
        >>> normalize_text("  Hello,  World!  ")
        'hello, world!'
    """
    if not text:
        return ""
    
    # 1. 去除 BOM（Byte Order Mark）
    text = text.lstrip("\ufeff")
    
    # 2. Unicode 规范化：把"全角"字母转成"半角"，统一编码形式
    #    比如：Ａ（全角A）→ A（半角A）
    text = unicodedata.normalize("NFKC", text)
    
    # 3. 合并连续空白（多个空格、制表符、换行符 → 一个空格）
    text = re.sub(r"\s+", " ", text)
    
    # 4. 去除首尾空白
    text = text.strip()
    
    # 5. 转小写（英文部分统一大小写）
    text = text.lower()
    
    return text


def generate_cache_key(
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    extra_context: str = "",
) -> str:
    """
    【生成缓存键】— 用于服务端缓存匹配
    
    将所有影响 AI 输出的因素组合在一起，生成唯一的哈希值。
    相同输入 → 相同缓存键 → 命中服务端缓存。
    
    参数:
        model: 模型名称
        system_prompt: 系统提示词
        user_message: 用户消息
        temperature: 温度参数（必须固定）
        max_tokens: 最大 token 数
    
    返回:
        SHA256 哈希字符串（64 位十六进制字符）
    """
    # 将所有参数拼接成一个长字符串
    # 分隔符 "|||" 防止边界混淆（比如 model+prompt 和 model_prompt 的区别）
    raw_key = "|||".join([
        model,
        normalize_text(system_prompt),
        normalize_text(user_message),
        str(temperature),
        str(max_tokens),
        normalize_text(extra_context),
    ])
    
    # 计算 SHA256 哈希
    # 哈希的特点是：相同输入 → 相同输出；不同输入 → 完全不同的输出
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_memory_cache_key(
    prompt_name: str,
    model: str,
    normalized_input: str,
) -> str:
    """
    【生成内存缓存键】— 用于本地内存缓存
    
    比服务端缓存键更轻量，只包含区分不同请求必须的信息。
    
    参数:
        prompt_name: 提示词名称
        model: 模型名称
        normalized_input: 已经标准化的用户输入
    
    返回:
        简化的缓存键字符串
    """
    return f"{prompt_name}:{model}:{hashlib.md5(normalized_input.encode()).hexdigest()}"
