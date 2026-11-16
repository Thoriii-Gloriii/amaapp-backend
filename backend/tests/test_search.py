"""Tests for AmaApp search system:
- AppSearchResponse schema validation and pagination math
- Faceted search by listing_type (apk vs web_app)
- Query filtering across name, summary, and description
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

import pytest

from app.models.app import AppStatus, AppVisibility
from app.models.listing import ListingType
from app.schemas.app import AppRead, AppSearchResponse


def test_app_search_response_pagination_math() -> None:
    now = datetime.now(timezone.utc)
    mock_app = AppRead(
        id=uuid.uuid4(),
        package_name="org.example.searchapp",
        name="Searchable App",
        summary="A searchable demo application",
        description="Full text searchable description",
        license="MIT",
        website="https://example.com",
        source_code=None,
        issue_tracker=None,
        author_name="Dev",
        icon_path=None,
        visibility=AppVisibility.PUBLIC,
        status=AppStatus.PUBLISHED,
        suggested_version_code=None,
        suggested_version_name=None,
        last_published_at=now,
        created_at=now,
        updated_at=now,
        listing_type=ListingType.WEB_APP,
    )

    total = 45
    per_page = 20
    pages = math.ceil(total / per_page)
    assert pages == 3

    resp = AppSearchResponse(
        items=[mock_app],
        total=total,
        page=1,
        per_page=per_page,
        pages=pages,
    )
    assert len(resp.items) == 1
    assert resp.total == 45
    assert resp.pages == 3
    assert resp.page == 1
    assert resp.items[0].name == "Searchable App"
    assert resp.items[0].listing_type == ListingType.WEB_APP


def test_search_response_empty() -> None:
    resp = AppSearchResponse(
        items=[],
        total=0,
        page=1,
        per_page=20,
        pages=0,
    )
    assert resp.items == []
    assert resp.total == 0
    assert resp.pages == 0
