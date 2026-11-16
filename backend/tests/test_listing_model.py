"""Tests for AmaApp listing model additions:
- ListingType enum (apk, web_app)
- WebAppListing model and schemas
- Debug build labeling (is_debug_build, vibe_tool, changelog)
- Warning field in API responses ("debug build, unreviewed")
- Permission checks: a user must not edit another user's listing
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import HttpUrl

from app.models.apk import Apk, ApkStatus
from app.models.app import App, AppStatus, AppVisibility
from app.models.listing import ListingType, WebAppListing
from app.models.user import User, UserRole
from app.schemas.app import (
    ApkRead,
    ApkUpdate,
    AppCreateWebApp,
    AppDetail,
    AppRead,
    WebAppListingCreate,
    WebAppListingRead,
)
from app.services.app_permissions import can_manage_app, is_owner_or_admin


def test_listing_type_enum() -> None:
    assert ListingType.APK == "apk"
    assert ListingType.WEB_APP == "web_app"
    assert ListingType("apk") == ListingType.APK
    assert ListingType("web_app") == ListingType.WEB_APP


def test_apk_debug_build_warning() -> None:
    """Show a clear 'debug build, unreviewed' warning field in the API response."""
    # Debug build that is unreviewed
    apk_debug_unreviewed = ApkRead(
        id=uuid.uuid4(),
        app_id=uuid.uuid4(),
        file_name="app-debug.apk",
        size_bytes=1024,
        sha256="a" * 64,
        version_code=1,
        version_name="1.0-debug",
        min_sdk=24,
        target_sdk=34,
        signer_sha256="b" * 64,
        permissions=[],
        native_code=[],
        status=ApkStatus.PENDING_REVIEW,
        rejection_reason=None,
        published_at=None,
        created_at="2026-11-16T00:00:00Z",
        is_debug_build=True,
        vibe_tool="Cursor + Claude 3.7",
        changelog="Fixed crash on start",
    )
    assert apk_debug_unreviewed.is_debug_build is True
    assert apk_debug_unreviewed.vibe_tool == "Cursor + Claude 3.7"
    assert apk_debug_unreviewed.changelog == "Fixed crash on start"
    assert apk_debug_unreviewed.warning == "debug build, unreviewed"

    # Debug build that is published
    apk_debug_published = ApkRead(
        id=uuid.uuid4(),
        app_id=uuid.uuid4(),
        file_name="app-debug.apk",
        size_bytes=1024,
        sha256="c" * 64,
        version_code=2,
        version_name="1.1-debug",
        min_sdk=24,
        target_sdk=34,
        signer_sha256="d" * 64,
        permissions=[],
        native_code=[],
        status=ApkStatus.PUBLISHED,
        rejection_reason=None,
        published_at="2026-11-16T00:00:00Z",
        created_at="2026-11-16T00:00:00Z",
        is_debug_build=True,
    )
    assert apk_debug_published.warning == "debug build"

    # Non-debug build that is published
    apk_clean_published = ApkRead(
        id=uuid.uuid4(),
        app_id=uuid.uuid4(),
        file_name="app-release.apk",
        size_bytes=1024,
        sha256="e" * 64,
        version_code=3,
        version_name="1.2",
        min_sdk=24,
        target_sdk=34,
        signer_sha256="f" * 64,
        permissions=[],
        native_code=[],
        status=ApkStatus.PUBLISHED,
        rejection_reason=None,
        published_at="2026-11-16T00:00:00Z",
        created_at="2026-11-16T00:00:00Z",
        is_debug_build=False,
    )
    assert apk_clean_published.warning is None


def test_web_app_listing_schema() -> None:
    create_schema = AppCreateWebApp(
        name="My Vibe Web App",
        url=HttpUrl("https://my-vibe-app.vercel.app"),
        summary="A web app built with vibe coding",
        description="Full description here",
        tech_stack="Next.js + Tailwind",
        screenshot_keys=["screenshots/web_1.png"],
    )
    assert str(create_schema.url) == "https://my-vibe-app.vercel.app/"
    assert create_schema.tech_stack == "Next.js + Tailwind"
    assert len(create_schema.screenshot_keys) == 1


@pytest.mark.asyncio
async def test_permission_user_cannot_manage_another_users_listing() -> None:
    """Security check: A user must NOT be able to manage another user's listing."""
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    owner = SimpleNamespace(id=owner_id, role=UserRole.UPLOADER)
    other_user = SimpleNamespace(id=other_user_id, role=UserRole.UPLOADER)
    admin_user = SimpleNamespace(id=uuid.uuid4(), role=UserRole.ADMIN)

    app = SimpleNamespace(
        id=uuid.uuid4(),
        owner_id=owner_id,
        package_name="web.amaapp.vibecoding",
        listing_type=ListingType.WEB_APP,
    )

    # Fake db session returning no collaborator rows
    class DummyScalar:
        def scalar_one_or_none(self) -> Any:
            return None

    class DummyDb:
        async def execute(self, stmt: Any) -> DummyScalar:
            return DummyScalar()

    dummy_db = DummyDb()

    # Owner can manage
    assert await can_manage_app(dummy_db, owner, app) is True
    assert is_owner_or_admin(owner, app) is True

    # Admin can manage
    assert await can_manage_app(dummy_db, admin_user, app) is True
    assert is_owner_or_admin(admin_user, app) is True

    # Other user CANNOT manage
    assert await can_manage_app(dummy_db, other_user, app) is False
    assert is_owner_or_admin(other_user, app) is False
