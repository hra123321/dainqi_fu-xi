"""
============================================
 AI 调用服务 — 统一入口
============================================
【作用】
所有与 DeepSeek API 的交互都通过这个模块。
封装了：模型选择、提示词填充、缓存检查、API 调用、错误处理。

【调用方只需关心】
  result = await ai_service.call(prompt_name="general", difficulty="easy", question="...")
"""

import asyncio
import traceback

import httpx

from app.config import settings
from app.prompts.loader import get_prompt
from app.models.dispatch import get_model_for_difficulty
from app.cache.memory_cache import cache as memory_cache
from app.cache.cache_key import generate_cache_key, generate_memory_cache_key, normalize_text
from app.utils.logger import logger, record_api_error


class AIService:
    """
    【AI 调用服务】
    
    所有 AI 调用的统一入口，封装完整调用流程。
    """

    def __init__(self):
        # 创建可复用的 HTTP 客户端
        # 复用连接减少开销
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),  # 单次请求最多等 60 秒
            follow_redirects=True,
        )

    async def call(
        self,
        prompt_name: str,
        difficulty: str = "normal",
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> str:
        """
        【核心方法】— 调用 AI 并返回结果
        
        参数:
            prompt_name: 提示词名称（如 "general", "objective_mcq"）
            difficulty: 难度标签（决定用 Flash 还是 Pro）
            temperature: 温度（默认使用配置文件的固定值）
            max_tokens: 最大 token 数（默认使用配置文件的固定值）
            **kwargs: 提示词占位符的填充值
        
        返回:
            AI 返回的文本内容
        
        使用示例:
            result = await ai_service.call(
                "general", difficulty="easy",
                question="什么是欧姆定律？",
                knowledge_context="欧姆定律: I=U/R"
            )
        """
        # 使用默认值
        if temperature is None:
            temperature = settings.TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.MAX_TOKENS
        
        try:
            # ===== 步骤 1：确定模型 =====
            model = get_model_for_difficulty(difficulty)
            logger.info(f"[AI] 调用 {prompt_name} | 难度={difficulty} | 模型={model}")
            
            # ===== 步骤 2：加载并填充提示词 =====
            system_prompt = get_prompt(prompt_name, **kwargs)
            
            # ===== 步骤 3：检查内存缓存 =====
            # 生成缓存键
            normalized_input = normalize_text(str(kwargs))
            mem_key = generate_memory_cache_key(prompt_name, model, normalized_input)
            
            cached_result = memory_cache.get(mem_key)
            if cached_result is not None:
                logger.info(f"[AI] 缓存命中: {prompt_name}")
                return cached_result
            
            # ===== 步骤 4：调用 DeepSeek API =====
            result_text = await self._call_deepseek_api(
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # ===== 步骤 5：写入缓存 =====
            memory_cache.set(mem_key, result_text)
            
            return result_text
        
        except Exception as e:
            error_msg = f"AI 调用失败: {str(e)}"
            logger.error(error_msg)
            record_api_error("ai_service.call", str(model), error_msg, prompt_name)
            raise

    async def _call_deepseek_api(
        self,
        model: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        【调用 DeepSeek API】
        
        向 DeepSeek 发送聊天补全请求。
        DeepSeek 兼容 OpenAI 的 API 格式。
        
        API 请求格式说明:
        发送给 AI 的消息是一个列表，每条消息有 role 和 content：
        - {"role": "system", "content": "你是一个电气老师..."}
        - {"role": "user", "content": "请问什么是欧姆定律？"}
        
        参数固定（tempture/top_p 等）是为了：
        1. 确保相同输入得到相同输出
        2. 提高 DeepSeek 服务端缓存命中率
        """
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # 生成服务端缓存键（用于 DeepSeek 的原生缓存适配）
        cache_key = generate_cache_key(
            model=model,
            system_prompt=system_prompt,
            user_message="",  # 提示词已包含所有内容
            temperature=temperature,
            max_tokens=max_tokens,
        )
        headers["x-cache-key"] = cache_key
        
        # 构造请求体
        # 这里的所有参数都是固定值，提升缓存命中率
        request_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
            ],
            "temperature": temperature,
            "top_p": settings.TOP_P,
            "max_tokens": max_tokens,
            "frequency_penalty": settings.FREQUENCY_PENALTY,
            "presence_penalty": settings.PRESENCE_PENALTY,
        }
        
        # 发送请求
        response = await self._client.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=request_body,
        )
        
        # 检查响应状态
        if response.status_code != 200:
            error_detail = response.text[:500]
            raise Exception(
                f"API 返回错误 {response.status_code}: {error_detail}"
            )
        
        # 解析响应
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        return content

    async def close(self):
        """关闭 HTTP 客户端（释放连接）"""
        await self._client.aclose()


# ==================== 全局实例 ====================
ai_service = AIService()
