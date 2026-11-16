"""AmaApp ratings and comments models for listings."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.app import App
    from app.models.user import User


class Rating(Base, IdMixin, TimestampMixin):
    """User rating for a listing (1 to 5 stars).

    One rating per (user_id, app_id) pair; users can update their score.
    """
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "app_id", name="uq_rating_user_app"),
        CheckConstraint("score >= 1 AND score <= 5", name="ck_rating_score_range"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    app: Mapped["App"] = relationship("App", foreign_keys=[app_id])


class Comment(Base, IdMixin, TimestampMixin):
    """User comment or review on a listing, with optional reply threading."""
    __tablename__ = "comments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    app: Mapped["App"] = relationship("App", foreign_keys=[app_id])
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        remote_side="Comment.parent_id",
        cascade="all, delete-orphan",
    )
    parent: Mapped["Comment | None"] = relationship(
        "Comment",
        back_populates="replies",
        remote_side="Comment.id",
    )
