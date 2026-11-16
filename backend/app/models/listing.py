"""AmaApp listing model additions.

Adds:
  - ListingType enum  (apk | web_app) on App
  - is_debug_build, vibe_tool, changelog  on Apk
  - WebAppListing model for web-app-specific fields
  - is_unreviewed flag on App (always True for user uploads; cleared by admin)

This module is imported by backend/app/models/__init__.py so SQLAlchemy
discovers the new tables and the Alembic autogenerate run picks them up.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
import enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.app import App


class ListingType(str, enum.Enum):
    """Discriminator for the kind of listing.

    ``apk``     — an Android APK (or dual APK+IPA) hosted on AmaApp.
                  Linked to :class:`~app.models.apk.Apk` rows.
    ``web_app`` — a hosted web application (GitHub Pages, Vercel, etc.).
                  No binary upload; stores a URL + screenshots.
    """
    APK = "apk"
    WEB_APP = "web_app"


class WebAppListing(Base, IdMixin, TimestampMixin):
    """Extra fields that only apply to web-app listings.

    One-to-one with :class:`~app.models.app.App` via ``app_id``.
    Created together with the parent App row; never exists without one.
    """
    __tablename__ = "web_app_listings"
    __table_args__ = (
        UniqueConstraint("app_id", name="uq_web_app_listing_app"),
    )

    app_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The hosted URL — validated for HTTPS and checked against the URL
    # blocklist at submission time.
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # JSON list of screenshot storage keys (uploaded via the existing
    # app media endpoints, same path as APK screenshots).
    screenshot_keys: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Optional tech stack / framework hint shown on the listing page.
    tech_stack: Mapped[str | None] = mapped_column(String(255))

    # Whether the URL passed the admin URL reachability + blocklist check.
    # Null = not yet checked. False = blocked / unreachable. True = OK.
    url_check_passed: Mapped[bool | None] = mapped_column(Boolean)

    # relationship back to the parent App
    app: Mapped["App"] = relationship("App", back_populates="web_app_listing")
