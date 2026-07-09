"""自定义学科 API。"""

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ingestion_service import subject_ingestion_service
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
