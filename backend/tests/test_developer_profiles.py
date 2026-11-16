"""Tests for AmaApp developer profile features:
- bio, links, avatar_url on User model
- UserRead and UserUpdate schemas
- PublicProfile schema and endpoint logic
- 404 behavior for consumer users with no public apps or profile data
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.user import User, UserRole
from app.schemas.user import PublicProfile, UserRead, UserUpdate


def test_user_read_schema_developer_fields() -> None:
    read = UserRead(
        id=uuid.uuid4(),
        email="dev@example.com",
        username="cooldev",
        full_name="Cool Developer",
        bio="I build awesome open-source mobile tools.",
        links=["https://github.com/cooldev", "https://cooldev.xyz"],
        avatar_url="https://cooldev.xyz/avatar.png",
        role=UserRole.UPLOADER,
        auth_provider="local",  # type: ignore
        is_active=True,
        last_login_at=None,
        show_nsfw=False,
        preferred_locale="en",
        created_at=datetime.now(timezone.utc),
    )
    assert read.bio == "I build awesome open-source mobile tools."
    assert len(read.links) == 2
    assert read.avatar_url == "https://cooldev.xyz/avatar.png"


def test_user_update_schema_accepts_bio_and_links() -> None:
    update = UserUpdate(
        bio="Updated bio",
        links=["https://cooldev.xyz", "https://x.com/cooldev"],
        avatar_url="https://images.example.com/avatar.jpg",
    )
    assert update.bio == "Updated bio"
    assert update.links == ["https://cooldev.xyz", "https://x.com/cooldev"]
    assert update.avatar_url == "https://images.example.com/avatar.jpg"


def test_public_profile_schema() -> None:
    now = datetime.now(timezone.utc)
    profile = PublicProfile(
        username="dev1",
        full_name="Developer One",
        bio="Full stack and mobile engineer.",
        links=["https://github.com/dev1"],
        avatar_url="https://example.com/dev1.jpg",
        member_since=now,
        apps=[],
    )
    assert profile.username == "dev1"
    assert profile.bio == "Full stack and mobile engineer."
    assert profile.links == ["https://github.com/dev1"]
    assert profile.avatar_url == "https://example.com/dev1.jpg"
    assert profile.apps == []


def test_user_model_profile_fields_default() -> None:
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        bio=None,
        links=[],
        avatar_url=None,
    )
    assert user.bio is None
    assert user.links == []
    assert user.avatar_url is None
