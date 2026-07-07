import asyncio

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
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
        except httpx.TimeoutException:
            last_error = f"请求超时(第 {attempt + 1} 次)"
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)
        except Exception as error:
            last_error = str(error)
            if attempt < retry_count - 1:
                await asyncio.sleep(1)

    raise Exception(f"API 调用失败（已重试 {retry_count} 次）: {last_error}")
