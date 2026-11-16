"""Pydantic schemas for listing moderation reports."""
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportReason, ReportStatus


class ReportCreate(BaseModel):
    reason: ReportReason
    details: str | None = Field(default=None, max_length=2000)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    app_id: uuid.UUID
    reporter_id: uuid.UUID | None = None
    reason: ReportReason
    details: str | None = None
    status: ReportStatus
    admin_notes: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class ReportAdminUpdate(BaseModel):
    status: ReportStatus
    admin_notes: str | None = Field(default=None, max_length=2000)
