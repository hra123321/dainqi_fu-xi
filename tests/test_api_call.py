import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.skills.api_skills import ai_caller


class FakeResponse:
    status_code = 200

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}


class FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        assert url.endswith("/chat/completions")
        assert headers["Authorization"].startswith("Bearer ")
        assert json["model"] == "deepseek-v4-flash"
        return FakeResponse()


async def run_case():
    original_client = ai_caller.httpx.AsyncClient
    try:
        ai_caller.httpx.AsyncClient = lambda timeout=60.0: FakeClient()
        text = await ai_caller.call_deepseek(
            api_key="test-key",
            base_url="https://example.com",
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": "hello"}],
        )
        assert text == "ok"
    finally:
        ai_caller.httpx.AsyncClient = original_client


def main():
    asyncio.run(run_case())
    print("PASS: test_api_call")


if __name__ == "__main__":
    main()
