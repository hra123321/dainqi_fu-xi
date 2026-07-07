"""自定义学科联网发现与向量入库服务。"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List

import httpx

from app.config import settings
from app.services.ai_service import ai_service
from app.services.subject_service import subject_service
from app.vector_db.client import COURSE_MATERIALS, vector_db
from app.vector_db.processor import pdf_processor


class SubjectIngestionService:
    """把“学科名”扩展成可检索的本地知识数据。"""

    async def run_ingestion(self, job_id: str, subject_id: str) -> Dict:
        subject = subject_service.get_subject(subject_id, include_topics=False)
        subject_service.update_subject_status(subject_id, "running")
        subject_service.update_job(job_id, status="running", stage="search", message="正在联网搜索公开资料")

        try:
            sources = await self.search_sources(subject["name"])
            subject_service.update_job(job_id, sources_found=len(sources), message=f"找到 {len(sources)} 条候选资料")

            if not sources:
                raise RuntimeError("没有找到可用候选资料；请配置 SEARXNG_URL 或稍后重试")

            accepted_sources = [source for source in sources if self._is_public_candidate(source)]
            subject_service.update_job(
                job_id,
                stage="review",
                sources_accepted=len(accepted_sources),
                message=f"通过初筛 {len(accepted_sources)} 条公开候选资料",
            )

            topics = await self.extract_topics(subject["name"], accepted_sources)
            topic_count = subject_service.replace_topics(subject_id, topics, source="generated")

            chunks = self._build_text_chunks(subject, accepted_sources, topics)
            stored = self.store_chunks(subject, chunks)

            subject_service.update_job(
                job_id,
                status="done",
                stage="completed",
                message=f"入库完成：{topic_count} 个知识点，{stored} 个向量片段",
                chunks_stored=stored,
            )
            subject_service.update_subject_status(subject_id, "done")
            return subject_service.get_job(job_id)
        except Exception as exc:
            subject_service.update_subject_status(subject_id, "failed")
            return subject_service.update_job(
                job_id,
                status="failed",
                stage="failed",
                message=str(exc),
            )

    async def search_sources(self, subject_name: str) -> List[Dict]:
        if settings.SEARXNG_URL:
            results = await self._search_searxng(subject_name)
            if results:
                return results
        return await self._search_duckduckgo(subject_name)

    async def _search_searxng(self, subject_name: str) -> List[Dict]:
        url = settings.SEARXNG_URL.rstrip("/") + "/search"
        params = {"q": f"{subject_name} 课程 知识点 题目", "format": "json", "language": "zh-CN"}
        async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "summary": item.get("content", ""),
                "license": "public-web-candidate",
            }
            for item in payload.get("results", [])[:8]
            if item.get("url")
        ]

    async def _search_duckduckgo(self, subject_name: str) -> List[Dict]:
        params = {
            "q": f"{subject_name} 课程 知识点 题目",
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            payload = response.json()

        sources = []
        abstract = payload.get("AbstractText") or payload.get("Definition")
        abstract_url = payload.get("AbstractURL") or payload.get("DefinitionURL")
        if abstract and abstract_url:
            sources.append(
                {
                    "title": payload.get("Heading") or subject_name,
                    "url": abstract_url,
                    "summary": abstract,
                    "license": "public-web-candidate",
                }
            )

        for item in payload.get("RelatedTopics", [])[:8]:
            if "Topics" in item:
                nested_items = item.get("Topics", [])[:3]
            else:
                nested_items = [item]
            for nested in nested_items:
                if nested.get("FirstURL") and nested.get("Text"):
                    sources.append(
                        {
                            "title": nested.get("Text", "")[:80],
                            "url": nested["FirstURL"],
                            "summary": nested["Text"],
                            "license": "public-web-candidate",
                        }
                    )
        return sources[:8]

    async def extract_topics(self, subject_name: str, sources: List[Dict]) -> List[Dict]:
        context = json.dumps(sources, ensure_ascii=False, indent=2)
        response = await ai_service.call(
            prompt_name="subject_discovery",
            difficulty="hard",
            response_format={"type": "json_object"},
            output_schema_version="subject-discovery-v1",
            subject=subject_name,
            search_context=context[:6000],
        )
        payload = self._load_json(response)
        topics = payload.get("topics", [])
        if not isinstance(topics, list) or not topics:
            raise RuntimeError("DeepSeek 未返回可用知识点结构")
        return topics[:80]

    def store_chunks(self, subject: Dict, chunks: List[Dict]) -> int:
        if not chunks:
            return 0

        collection = vector_db.get_or_create_collection(COURSE_MATERIALS)
        model = pdf_processor._get_embedding_model()
        texts = [chunk["text"] for chunk in chunks]
        embeddings = model.encode(texts, show_progress_bar=False)
        ids = [chunk["id"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        collection.add(ids=ids, embeddings=embeddings.tolist(), metadatas=metadatas, documents=texts)
        return len(chunks)

    def _build_text_chunks(self, subject: Dict, sources: List[Dict], topics: List[Dict]) -> List[Dict]:
        chunks = []
        subject_id = subject["id"]
        for index, source in enumerate(sources):
            source_text = f"资料标题：{source.get('title', '')}\n资料摘要：{source.get('summary', '')}\n资料URL：{source.get('url', '')}"
            source_id = hashlib.sha256(source.get("url", "").encode("utf-8")).hexdigest()[:16]
            chunks.append(
                {
                    "id": f"{subject_id}_source_{source_id}_{index}",
                    "text": source_text,
                    "metadata": {
                        "subject_id": subject_id,
                        "subject": subject["name"],
                        "source_id": source_id,
                        "source": source.get("url", ""),
                        "title": source.get("title", ""),
                        "license": source.get("license", "public-web-candidate"),
                        "topic": "",
                        "chunk_type": "source_summary",
                        "hash": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                    },
                }
            )

        for index, topic in enumerate(topics):
            text = f"{subject['name']} 知识点：{topic.get('name', '')}\n难度：{topic.get('difficulty', 3)}星\n考试重要性：{topic.get('examImportance', 3)}星\n工程重要性：{topic.get('engineeringImportance', 3)}星"
            chunks.append(
                {
                    "id": f"{subject_id}_topic_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}_{index}",
                    "text": text,
                    "metadata": {
                        "subject_id": subject_id,
                        "subject": subject["name"],
                        "source_id": "deepseek-topic-discovery",
                        "source": "DeepSeek structured extraction from reviewed search summaries",
                        "title": topic.get("name", ""),
                        "license": "generated-summary",
                        "topic": topic.get("name", ""),
                        "chunk_type": "topic_outline",
                        "hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    },
                }
            )
        return chunks

    def _is_public_candidate(self, source: Dict) -> bool:
        url = source.get("url", "").lower()
        blocked = ("login", "signin", "vip", "paywall", "passport", "captcha")
        return bool(url.startswith("http")) and not any(token in url for token in blocked)

    def _load_json(self, text: str) -> Dict:
        stripped = text.strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            stripped = stripped[start : end + 1]
        return json.loads(stripped)


subject_ingestion_service = SubjectIngestionService()
