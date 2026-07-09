"""知识库自成长评估门禁。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.services.knowledge_model_service import knowledge_model_service


OPEN_LICENSE_MARKERS = (
    "cc-by",
    "cc by",
    "creative commons",
    "open access",
    "public domain",
    "公开",
    "开放",
    "public-web-candidate",
    "generated-summary",
)


@dataclass
class GateResult:
    passed: bool
    score: int
    status: str
    checks: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "status": self.status,
            "checks": self.checks,
        }


class GrowthGateService:
    """把候选知识内容拦在正式库之前。"""

    def evaluate_source(self, source: dict[str, Any]) -> GateResult:
        checks = [
            self._check_required("title", source.get("title")),
            self._check_license(source.get("license", "")),
            self._check_hash(source.get("content_hash") or source.get("contentHash")),
            self._check_blocked_url(source.get("url", "")),
        ]
        return self._summarize(checks)

    def evaluate_node(self, node: dict[str, Any]) -> GateResult:
        checks = [
            self._check_required("name", node.get("name")),
            self._check_star("difficulty", node.get("difficulty")),
            self._check_star("exam_importance", node.get("exam_importance")),
            self._check_star("engineering_importance", node.get("engineering_importance")),
            self._check_formula_risk(node.get("name", "")),
        ]
        return self._summarize(checks)

    def publish_source_if_passed(self, source_id: str) -> dict[str, Any]:
        source = knowledge_model_service.get_source(source_id)
        result = self.evaluate_source(source)
        updated_status = "approved" if result.passed else result.status
        updated = knowledge_model_service.update_source_quality(source_id, updated_status)
        return {"source": updated, "gate": result.to_dict()}

    def publish_node_if_passed(self, node_id: str) -> dict[str, Any]:
        node = knowledge_model_service.get_node(node_id)
        result = self.evaluate_node(node)
        updated_status = "approved" if result.passed else result.status
        updated = knowledge_model_service.update_node_quality(node_id, updated_status)
        return {"node": updated, "gate": result.to_dict()}

    def _summarize(self, checks: list[dict[str, Any]]) -> GateResult:
        score = sum(item["score"] for item in checks)
        failed_required = any(item["required"] and not item["passed"] for item in checks)
        needs_review = any(item["status"] == "needs_review" for item in checks)
        passed = not failed_required and not needs_review and score >= 80
        status = "approved" if passed else "needs_review" if needs_review else "rejected"
        return GateResult(passed=passed, score=score, status=status, checks=checks)

    def _check_required(self, field: str, value) -> dict[str, Any]:
        passed = bool(str(value or "").strip())
        return {
            "name": f"required:{field}",
            "passed": passed,
            "required": True,
            "score": 25 if passed else 0,
            "status": "candidate" if passed else "rejected",
            "message": "必填字段存在" if passed else f"缺少必填字段 {field}",
        }

    def _check_license(self, license_text: str) -> dict[str, Any]:
        lowered = license_text.lower()
        passed = any(marker in lowered for marker in OPEN_LICENSE_MARKERS)
        return {
            "name": "license",
            "passed": passed,
            "required": True,
            "score": 25 if passed else 0,
            "status": "candidate" if passed else "needs_review",
            "message": "许可描述可接受" if passed else "许可不明确，需要人工复核",
        }

    def _check_hash(self, value: str) -> dict[str, Any]:
        passed = bool(re.fullmatch(r"[a-f0-9]{64}", str(value or "")))
        return {
            "name": "content_hash",
            "passed": passed,
            "required": True,
            "score": 25 if passed else 0,
            "status": "candidate" if passed else "rejected",
            "message": "内容哈希有效" if passed else "缺少有效 SHA256 哈希",
        }

    def _check_blocked_url(self, url: str) -> dict[str, Any]:
        lowered = url.lower()
        blocked = ("login", "signin", "vip", "paywall", "passport", "captcha")
        passed = not any(token in lowered for token in blocked)
        return {
            "name": "blocked_url",
            "passed": passed,
            "required": True,
            "score": 25 if passed else 0,
            "status": "candidate" if passed else "rejected",
            "message": "链接未命中登录/付费/验证码风险" if passed else "链接疑似需要登录、付费或验证码",
        }

    def _check_star(self, field: str, value) -> dict[str, Any]:
        passed = isinstance(value, int) and 1 <= value <= 5
        return {
            "name": f"star:{field}",
            "passed": passed,
            "required": True,
            "score": 20 if passed else 0,
            "status": "candidate" if passed else "rejected",
            "message": "星级在 1-5 范围内" if passed else f"{field} 星级非法",
        }

    def _check_formula_risk(self, text: str) -> dict[str, Any]:
        risky = bool(re.search(r"\\frac|\\sum|\\int|\$|\^|_", text))
        return {
            "name": "formula_review",
            "passed": not risky,
            "required": False,
            "score": 20 if not risky else 0,
            "status": "candidate" if not risky else "needs_review",
            "message": "未发现公式复核风险" if not risky else "含公式符号，发布前需要公式渲染复核",
        }


growth_gate_service = GrowthGateService()
