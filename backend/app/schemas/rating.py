"""Pydantic schemas for ratings and comments on listings."""
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    score: int = Field(ge=1, le=5)


class RatingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    app_id: uuid.UUID
    score: int
    created_at: datetime
    updated_at: datetime


class RatingSummary(BaseModel):
    app_id: uuid.UUID
    average_score: float = 0.0
    total_ratings: int = 0
    distribution: dict[int, int] = Field(
        default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )
    user_rating: int | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    parent_id: uuid.UUID | None = None


class CommentAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    avatar_url: str | None = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    app_id: uuid.UUID
    user_id: uuid.UUID
    author: CommentAuthor | None = None
    parent_id: uuid.UUID | None = None
    body: str
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
