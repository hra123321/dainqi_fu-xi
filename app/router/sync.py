"""多端同步 API。"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.sync_service import sync_service


router = APIRouter(prefix="/api/v1/sync", tags=["多端同步"])


class SyncEventRequest(BaseModel):
    id: str = Field(default="", max_length=80)
    type: str = Field(..., max_length=40)
    payload: dict[str, Any] = Field(default_factory=dict)
    client_updated_at: int = Field(default=0)


class SyncPushRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=120)
    events: list[SyncEventRequest] = Field(default_factory=list)


class SyncPullRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=120)
    since: int = Field(default=0, ge=0)


@router.post("/push")
async def push_sync_events(req: SyncPushRequest):
    try:
        return sync_service.push(
            device_id=req.device_id,
            events=[event.model_dump() for event in req.events],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/pull")
async def pull_sync_state(req: SyncPullRequest):
    try:
        return sync_service.pull(device_id=req.device_id, since=req.since)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
