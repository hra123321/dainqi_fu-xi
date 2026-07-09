"""
AI 调用服务 — 统一入口
"""

import json
from typing import Dict, Optional

import httpx

from app.cache.cache_key import generate_cache_key, generate_memory_cache_key, normalize_text
from app.cache.memory_cache import cache as memory_cache
from app.config import settings
from app.models.dispatch import get_model_for_difficulty, is_pro_model
from app.prompts.loader import get_prompt
from app.security import require_api_key
from app.utils.logger import logger, record_api_error


class AIService:
    """统一封装 DeepSeek API 调用和缓存策略。"""

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            follow_redirects=True,
        )

    async def call(
        self,
        prompt_name: str,
        difficulty: str = "normal",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None,
        output_schema_version: str = "",
        **kwargs,
    ) -> str:
        if temperature is None:
            temperature = settings.TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.MAX_TOKENS

        try:
            model = get_model_for_difficulty(difficulty)
            thinking_enabled = is_pro_model(difficulty)
            reasoning_effort = "high" if thinking_enabled else None
            system_prompt = get_prompt(prompt_name, **kwargs)

            logger.info(
                f"[AI] 调用 {prompt_name} | 难度={difficulty} | 模型={model} | 思考={thinking_enabled}"
            )

            cache_context = {
                "prompt_name": prompt_name,
                "model": model,
                "thinking_enabled": thinking_enabled,
                "response_format": response_format or {},
                "output_schema_version": output_schema_version,
                "prompt_version": settings.PROMPT_VERSION,
                "question_schema_version": settings.QUESTION_SCHEMA_VERSION,
                "kwargs": kwargs,
            }
            normalized_input = normalize_text(json.dumps(cache_context, ensure_ascii=False, sort_keys=True))
            mem_key = generate_memory_cache_key(prompt_name, model, normalized_input)
            cached_result = memory_cache.get(mem_key)
            if cached_result is not None:
                logger.info(f"[AI] 缓存命中: {prompt_name}")
                return cached_result

            result_text = await self._call_deepseek_api(
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_enabled=thinking_enabled,
                reasoning_effort=reasoning_effort,
                response_format=response_format,
                cache_context=normalized_input,
            )

            memory_cache.set(mem_key, result_text)
            return result_text

        except Exception as exc:
            error_msg = f"AI 调用失败: {str(exc)}"
            logger.error(error_msg)
            record_api_error("ai_service.call", get_model_for_difficulty(difficulty), error_msg, prompt_name)
            raise

    async def _call_deepseek_api(
        self,
        model: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        thinking_enabled: bool,
        reasoning_effort: Optional[str],
        response_format: Optional[Dict],
        cache_context: str,
    ) -> str:
        api_key = require_api_key(settings.DEEPSEEK_API_KEY)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        cache_key = generate_cache_key(
            model=model,
            system_prompt=system_prompt,
            user_message="请根据上面的要求开始",
            temperature=temperature if not thinking_enabled else 0.0,
            max_tokens=max_tokens,
            extra_context=cache_context,
        )
        headers["x-cache-key"] = cache_key

        request_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上面的要求开始"},
            ],
            "max_tokens": max_tokens,
        }

        if response_format:
            request_body["response_format"] = response_format

        if thinking_enabled:
            request_body["thinking"] = {"type": "enabled"}
            request_body["reasoning_effort"] = reasoning_effort or "high"
        else:
            request_body["thinking"] = {"type": "disabled"}
            request_body["temperature"] = temperature
            request_body["top_p"] = settings.TOP_P

        logger.info(
            f"[AI] 发送请求: model={model}, thinking={thinking_enabled}, response_format={bool(response_format)}"
        )
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
