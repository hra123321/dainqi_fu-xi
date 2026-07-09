"""自定义学科 API。"""

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ingestion_service import subject_ingestion_service
from app.services.knowledge_model_service import knowledge_model_service
from app.services.subject_service import subject_service


router = APIRouter(prefix="/api", tags=["学科"])


class SubjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    short: str = Field(default="", max_length=20)
    icon: str = Field(default="📘", max_length=8)
    aliases: List[str] = Field(default_factory=list)


class DomainCreateRequest(SubjectCreateRequest):
    domain_type: str = Field(default="course", max_length=20)
    version: str = Field(default="", max_length=80)
    learning_goal: str = Field(default="", max_length=300)


class KnowledgeNodeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    parent_id: str = Field(default="", max_length=80)
    node_type: str = Field(default="knowledge", max_length=30)
    difficulty: int = Field(default=3, ge=1, le=5)
    exam_importance: int = Field(default=3, ge=1, le=5)
    engineering_importance: int = Field(default=3, ge=1, le=5)
    source_id: str = Field(default="", max_length=80)
    quality_status: str = Field(default="candidate", max_length=30)
    version: str = Field(default="", max_length=80)


class KnowledgeSourceRequest(BaseModel):
    domain_id: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=200)
    url: str = Field(default="", max_length=500)
    author: str = Field(default="", max_length=120)
    license_name: str = Field(default="", max_length=120)
    source_type: str = Field(default="web", max_length=30)
    content: str = Field(default="", max_length=10000)
    quality_status: str = Field(default="candidate", max_length=30)


@router.get("/subjects")
async def list_subjects():
    return {"subjects": subject_service.list_subjects(include_topics=True)}


@router.post("/subjects")
async def create_subject(req: SubjectCreateRequest):
    try:
        subject = subject_service.create_subject(
            name=req.name,
            short=req.short,
            icon=req.icon,
            aliases=req.aliases,
        )
        return {"success": True, "subject": subject}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/v1/domains")
async def list_domains():
    return {"domains": subject_service.list_domains(include_topics=True)}


@router.post("/v1/domains")
async def create_domain(req: DomainCreateRequest):
    try:
        domain = subject_service.create_domain(
            name=req.name,
            domain_type=req.domain_type,
            short=req.short,
            icon=req.icon,
            aliases=req.aliases,
            version=req.version,
            learning_goal=req.learning_goal,
        )
        return {"success": True, "domain": domain}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/v1/domains/{domain_id}")
async def get_domain(domain_id: str):
    try:
        return {"domain": subject_service.get_domain(domain_id, include_topics=True)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/v1/domains/{domain_id}/knowledge-tree")
async def get_domain_knowledge_tree(domain_id: str):
    try:
        subject_service.get_domain(domain_id, include_topics=False)
        return {"domain_id": domain_id, "nodes": knowledge_model_service.list_tree(domain_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/v1/domains/{domain_id}/knowledge-tree")
async def upsert_domain_knowledge_node(domain_id: str, req: KnowledgeNodeRequest):
    try:
        subject_service.get_domain(domain_id, include_topics=False)
        node = knowledge_model_service.upsert_node(
            domain_id=domain_id,
            name=req.name,
            parent_id=req.parent_id,
            node_type=req.node_type,
            difficulty=req.difficulty,
            exam_importance=req.exam_importance,
            engineering_importance=req.engineering_importance,
            source_id=req.source_id,
            quality_status=req.quality_status,
            version=req.version,
        )
        return {"success": True, "node": node}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/v1/sources")
async def register_knowledge_source(req: KnowledgeSourceRequest):
    try:
        subject_service.get_domain(req.domain_id, include_topics=False)
        source = knowledge_model_service.register_source(
            domain_id=req.domain_id,
            title=req.title,
            url=req.url,
            author=req.author,
            license_name=req.license_name,
            source_type=req.source_type,
            content=req.content,
            quality_status=req.quality_status,
        )
        return {"success": True, "source": source}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/v1/domains/{domain_id}/sources")
async def list_domain_sources(domain_id: str):
    try:
        subject_service.get_domain(domain_id, include_topics=False)
        return {"domain_id": domain_id, "sources": knowledge_model_service.list_sources(domain_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/subjects/{subject_id}/topics")
async def get_subject_topics(subject_id: str):
    try:
        return {"subject": subject_service.get_subject(subject_id, include_topics=False), "topics": subject_service.get_topics(subject_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/subjects/{subject_id}/ingest")
async def start_subject_ingestion(subject_id: str):
    try:
        job = subject_service.create_job(subject_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    asyncio.create_task(subject_ingestion_service.run_ingestion(job["id"], subject_id))
    return {"success": True, "job": job}


@router.get("/ingestion-jobs/{job_id}")
async def get_ingestion_job(job_id: str):
    try:
        return {"job": subject_service.get_job(job_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
