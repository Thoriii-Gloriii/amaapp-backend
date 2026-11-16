"""Ratings and comments API endpoints for AmaApp listings."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, get_current_user, get_current_user_optional
from app.core.rate_limit import limiter
from app.models.app import App
from app.models.rating import Comment, Rating
from app.models.user import User, UserRole
from app.schemas.rating import (
    CommentAuthor,
    CommentCreate,
    CommentRead,
    RatingCreate,
    RatingRead,
    RatingSummary,
)

router = APIRouter()


# --------------------------------------------------------------------------
# Ratings
# --------------------------------------------------------------------------
@router.post("/apps/{app_id}/ratings", response_model=RatingRead)
@router.post("/listings/{app_id}/ratings", response_model=RatingRead)
@limiter.limit("20/minute")
async def rate_app(
    app_id: uuid.UUID,
    payload: RatingCreate,
    db: DbSession,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> RatingRead:
    """Submit or update a 1–5 star rating for an app listing."""
    app = (await db.execute(select(App).where(App.id == app_id))).scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    existing = (
        await db.execute(
            select(Rating).where(Rating.app_id == app.id, Rating.user_id == user.id)
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.score = payload.score
        rating_obj = existing
    else:
        rating_obj = Rating(
            user_id=user.id,
            app_id=app.id,
            score=payload.score,
        )
        db.add(rating_obj)

    await db.flush()
    return RatingRead.model_validate(rating_obj)


@router.get("/apps/{app_id}/ratings", response_model=RatingSummary)
@router.get("/listings/{app_id}/ratings", response_model=RatingSummary)
async def get_app_ratings(
    app_id: uuid.UUID,
    db: DbSession,
    user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> RatingSummary:
    """Get the aggregate rating summary (average, total count, distribution) for a listing."""
    app = (await db.execute(select(App).where(App.id == app_id))).scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    # Aggregate stats
    rows = (
        await db.execute(
            select(Rating.score, func.count(Rating.id))
            .where(Rating.app_id == app.id)
            .group_by(Rating.score)
        )
    ).all()

    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_ratings = 0
    total_score = 0
    for score_val, cnt in rows:
        distribution[score_val] = cnt
        total_ratings += cnt
        total_score += score_val * cnt

    avg_score = round(total_score / total_ratings, 2) if total_ratings > 0 else 0.0

    user_rating: int | None = None
    if user is not None:
        user_row = (
            await db.execute(
                select(Rating.score).where(
                    Rating.app_id == app.id, Rating.user_id == user.id
                )
            )
        ).scalar_one_or_none()
        user_rating = user_row

    return RatingSummary(
        app_id=app.id,
        average_score=avg_score,
        total_ratings=total_ratings,
        distribution=distribution,
        user_rating=user_rating,
    )


# --------------------------------------------------------------------------
# Comments
# --------------------------------------------------------------------------
@router.post(
    "/apps/{app_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/listings/{app_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/hour")
async def add_comment(
    app_id: uuid.UUID,
    payload: CommentCreate,
    db: DbSession,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> CommentRead:
    """Post a comment or review on an app listing. Rate-limited to 10/hour."""
    app = (await db.execute(select(App).where(App.id == app_id))).scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    if payload.parent_id is not None:
        parent = (
            await db.execute(
                select(Comment).where(
                    Comment.id == payload.parent_id, Comment.app_id == app.id
                )
            )
        ).scalar_one_or_none()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found"
            )

    comment = Comment(
        app_id=app.id,
        user_id=user.id,
        parent_id=payload.parent_id,
        body=payload.body.strip(),
        is_deleted=False,
    )
    db.add(comment)
    await db.flush()

    return CommentRead(
        id=comment.id,
        app_id=comment.app_id,
        user_id=comment.user_id,
        author=CommentAuthor(
            id=user.id, username=user.username, avatar_url=user.avatar_url
        ),
        parent_id=comment.parent_id,
        body=comment.body,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/apps/{app_id}/comments", response_model=list[CommentRead])
@router.get("/listings/{app_id}/comments", response_model=list[CommentRead])
async def list_comments(
    app_id: uuid.UUID,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CommentRead]:
    """List comments on a listing in chronological order."""
    stmt = (
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.app_id == app_id)
        .order_by(Comment.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    results: list[CommentRead] = []
    for c in rows:
        author = (
            CommentAuthor(
                id=c.user.id, username=c.user.username, avatar_url=c.user.avatar_url
            )
            if c.user
            else None
        )
        display_body = "[deleted]" if c.is_deleted else c.body
        results.append(
            CommentRead(
                id=c.id,
                app_id=c.app_id,
                user_id=c.user_id,
                author=author,
                parent_id=c.parent_id,
                body=display_body,
                is_deleted=c.is_deleted,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return results


@router.delete("/comments/{comment_id}", response_model=dict)
async def delete_comment(
    comment_id: uuid.UUID,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Delete a comment (allowed by the comment's author or an administrator)."""
    comment = (
        await db.execute(select(Comment).where(Comment.id == comment_id))
    ).scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's comment",
        )

    comment.is_deleted = True
    comment.body = "[deleted]"
    await db.flush()
    return {"status": "deleted"}
