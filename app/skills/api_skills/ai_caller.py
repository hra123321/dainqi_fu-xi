"""
============================================
 AI 接口调用 Skill — 调用 DeepSeek API 的核心逻辑
============================================
【作用】
封装 DeepSeek API 的 HTTP 调用细节。
包括：请求构造、重试策略、错误处理。

【白名单】
本文件位于 app/skills/ 下，AI 可自动修改优化。
"""

import asyncio
import json

import httpx


async def call_deepseek(
    api_key: str,
    base_url: str,
    model: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 0.9,
    retry_count: int = 3,
) -> str:
    """
    【调用 DeepSeek API】
    
    发送聊天请求到 DeepSeek 并返回响应文本。
    内置重试机制，网络不稳定时自动重试。
    
    参数:
        api_key: API 密钥
        base_url: API 基础地址
        model: 模型名称
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数
        top_p: Top-P 采样
        retry_count: 失败重试次数
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }
    
    last_error = None
    
    for attempt in range(retry_count):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        
        except httpx.TimeoutException:
            last_error = f"超时(第{attempt+1}次)"
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s
        
        except Exception as e:
            last_error = str(e)
            if attempt < retry_count - 1:
                await asyncio.sleep(1)
    
    raise Exception(f"API 调用失败（已重试{retry_count}次）: {last_error}")
