"""Security helpers that keep secrets out of code, logs, and clients."""

import re
from pathlib import Path
from typing import Iterable


SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
PLACEHOLDER_VALUES = {
    "",
    "your-api-key",
    "your_deepseek_api_key",
    "replace-me",
}


def require_api_key(api_key: str) -> str:
    """Return a usable API key or raise an error without exposing its value."""
    normalized = api_key.strip()
    if normalized.lower() in PLACEHOLDER_VALUES:
        raise RuntimeError("DeepSeek API Key 未配置，请在本机 .env 中设置后重试。")
    if not normalized.startswith("sk-") or len(normalized) < 20:
        raise RuntimeError("DeepSeek API Key 格式无效，请重新生成并更新本机 .env。")
    return normalized


def find_committed_secrets(paths: Iterable[Path]) -> list[str]:
    """Return relative paths containing key-shaped strings."""
    findings: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if SECRET_PATTERN.search(content):
            findings.append(path.as_posix())
    return findings
