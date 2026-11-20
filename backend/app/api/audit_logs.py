from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import get_db
from app.dependencies import has_permission
from app.services.audit_log_service import query_audit, cleanup_audit
from app.core.rate_limit import limiter

router = APIRouter()


class CleanupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dry_run: bool = True
    limit: int = Field(100, ge=1, le=100)


@router.get("")
@limiter.limit("30/minute")
async def list_audit(request: Request, page: int = Query(1, ge=1, le=10000), limit: int = Query(25, ge=1, le=100),
                     category: str | None = Query(None, max_length=50), action: str | None = Query(None, max_length=100),
                     user_id: int | None = Query(None, gt=0), target_type: str | None = Query(None, max_length=50),
                     target_id: str | None = Query(None, max_length=100), status: str | None = Query(None, max_length=20),
                     request_id: str | None = Query(None, max_length=100), since: datetime | None = None,
                     until: datetime | None = None, db: AsyncSession = Depends(get_db),
                     actor=Depends(has_permission([1]))):
    def utc(value):
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value and value.tzinfo else value
    return await query_audit(db, request, actor, page=page, limit=limit, category=category, action=action,
        user_id=user_id, target_type=target_type, target_id=target_id, status=status, request_id=request_id,
        since=utc(since), until=utc(until))


@router.post("/cleanup")
@limiter.limit("2/minute")
async def cleanup(request: Request, data: CleanupRequest, db: AsyncSession = Depends(get_db),
                  actor=Depends(has_permission([1]))):
    return await cleanup_audit(db, request, actor, dry_run=data.dry_run, limit=data.limit)
