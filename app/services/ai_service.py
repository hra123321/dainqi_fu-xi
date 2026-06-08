"""
============================================
 AI 调用服务 — 统一入口
============================================
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
    """AI 调用服务"""

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
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
        if temperature is None:
            temperature = settings.TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.MAX_TOKENS

        try:
            model = get_model_for_difficulty(difficulty)
            logger.info(f"[AI] 调用 {prompt_name} | 难度={difficulty} | 模型={model}")

            system_prompt = get_prompt(prompt_name, **kwargs)

            # 检查内存缓存
            normalized_input = normalize_text(str(kwargs))
            mem_key = generate_memory_cache_key(prompt_name, model, normalized_input)
            cached_result = memory_cache.get(mem_key)
            if cached_result is not None:
                logger.info(f"[AI] 缓存命中: {prompt_name}")
                return cached_result

            # 调用 DeepSeek API
            result_text = await self._call_deepseek_api(
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            memory_cache.set(mem_key, result_text)
            return result_text

        except Exception as e:
            error_msg = f"AI 调用失败: {str(e)}"
            logger.error(error_msg)
            record_api_error("ai_service.call", "", error_msg, prompt_name)
            raise

    async def _call_deepseek_api(
        self,
        model: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }

        cache_key = generate_cache_key(
            model=model,
            system_prompt=system_prompt,
            user_message="请开始",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        headers["x-cache-key"] = cache_key

        request_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上面的要求开始"},
            ],
            "temperature": temperature,
            "top_p": settings.TOP_P,
            "max_tokens": max_tokens,
            "frequency_penalty": settings.FREQUENCY_PENALTY,
            "presence_penalty": settings.PRESENCE_PENALTY,
        }

        logger.info(f"[AI] 发送请求: model={model}, temperature={temperature}, max_tokens={max_tokens}")
        response = await self._client.post(
            f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=request_body,
        )

        if response.status_code != 200:
            error_detail = response.text[:500]
            raise Exception(f"API 返回错误 {response.status_code}: {error_detail}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info(f"[AI] 响应成功: {len(content)} 字符")
        return content

    async def close(self):
        await self._client.aclose()


ai_service = AIService()
