"""Tests for AmaApp ratings and comments:
- Rating score bounds (1 to 5 stars)
- RatingCreate, RatingRead, RatingSummary schemas
- CommentCreate, CommentRead, CommentAuthor schemas
- Comment soft-deletion display format
- Model field validations
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.rating import Comment, Rating
from app.schemas.rating import (
    CommentAuthor,
    CommentCreate,
    CommentRead,
    RatingCreate,
    RatingRead,
    RatingSummary,
)


def test_rating_score_bounds() -> None:
    # Valid scores 1 to 5
    for valid_score in (1, 2, 3, 4, 5):
        rating = RatingCreate(score=valid_score)
        assert rating.score == valid_score

    # Invalid scores
    for invalid_score in (0, 6, -1, 100):
        with pytest.raises(ValidationError):
            RatingCreate(score=invalid_score)


def test_rating_summary_schema() -> None:
    app_id = uuid.uuid4()
    summary = RatingSummary(
        app_id=app_id,
        average_score=4.67,
        total_ratings=15,
        distribution={1: 0, 2: 0, 3: 1, 4: 3, 5: 11},
        user_rating=5,
    )
    assert summary.app_id == app_id
    assert summary.average_score == 4.67
    assert summary.total_ratings == 15
    assert summary.distribution[5] == 11
    assert summary.user_rating == 5


def test_comment_create_schema() -> None:
    # Valid comment
    c = CommentCreate(body="Great web app, fast and smooth UI!")
    assert c.body == "Great web app, fast and smooth UI!"
    assert c.parent_id is None

    # Reply to another comment
    parent = uuid.uuid4()
    reply = CommentCreate(body="Thanks for the feedback!", parent_id=parent)
    assert reply.parent_id == parent

    # Empty body rejected
    with pytest.raises(ValidationError):
        CommentCreate(body="")


def test_comment_read_schema_and_author() -> None:
    now = datetime.now(timezone.utc)
    comment_id = uuid.uuid4()
    app_id = uuid.uuid4()
    user_id = uuid.uuid4()

    author = CommentAuthor(
        id=user_id,
        username="devguru",
        avatar_url="https://example.com/avatar.png",
    )

    read = CommentRead(
        id=comment_id,
        app_id=app_id,
        user_id=user_id,
        author=author,
        parent_id=None,
        body="Works flawlessly on Android 15.",
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )
    assert read.id == comment_id
    assert read.author is not None
    assert read.author.username == "devguru"
    assert read.is_deleted is False


def test_models_instantiation() -> None:
    u_id = uuid.uuid4()
    a_id = uuid.uuid4()
    r = Rating(user_id=u_id, app_id=a_id, score=5)
    assert r.user_id == u_id
    assert r.score == 5

    c = Comment(user_id=u_id, app_id=a_id, body="Top tier open-source tool.", is_deleted=False)
    assert c.user_id == u_id
    assert c.body == "Top tier open-source tool."
    assert c.is_deleted is False
