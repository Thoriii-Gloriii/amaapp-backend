"""Tests for AmaApp listing reporting system:
- ReportReason and ReportStatus enums
- ReportCreate, ReportRead, ReportAdminUpdate schemas
- Report model instantiation and attributes
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.report import Report, ReportReason, ReportStatus
from app.schemas.report import ReportAdminUpdate, ReportCreate, ReportRead


def test_report_enums() -> None:
    assert ReportReason.MALWARE == "malware"
    assert ReportReason.SCAM == "scam"
    assert ReportReason.BROKEN == "broken"
    assert ReportReason.INAPPROPRIATE == "inappropriate"
    assert ReportReason.COPYRIGHT == "copyright"
    assert ReportReason.OTHER == "other"

    assert ReportStatus.PENDING == "pending"
    assert ReportStatus.RESOLVED == "resolved"
    assert ReportStatus.DISMISSED == "dismissed"


def test_report_create_schema() -> None:
    create = ReportCreate(
        reason=ReportReason.MALWARE,
        details="App requests suspicious SMS permissions and contacts malicious server.",
    )
    assert create.reason == ReportReason.MALWARE
    assert "suspicious SMS" in (create.details or "")

    with pytest.raises(ValidationError):
        ReportCreate(reason="nonexistent_reason")  # type: ignore


def test_report_read_schema() -> None:
    now = datetime.now(timezone.utc)
    report_id = uuid.uuid4()
    app_id = uuid.uuid4()
    reporter_id = uuid.uuid4()

    read = ReportRead(
        id=report_id,
        app_id=app_id,
        reporter_id=reporter_id,
        reason=ReportReason.SCAM,
        details="Demands payment upfront and provides no functionality",
        status=ReportStatus.PENDING,
        admin_notes=None,
        resolved_at=None,
        created_at=now,
    )
    assert read.id == report_id
    assert read.app_id == app_id
    assert read.reporter_id == reporter_id
    assert read.reason == ReportReason.SCAM
    assert read.status == ReportStatus.PENDING


def test_report_admin_update_schema() -> None:
    update = ReportAdminUpdate(
        status=ReportStatus.RESOLVED,
        admin_notes="App suspended and developer notified.",
    )
    assert update.status == ReportStatus.RESOLVED
    assert update.admin_notes == "App suspended and developer notified."


def test_report_model_defaults() -> None:
    app_id = uuid.uuid4()
    report = Report(
        app_id=app_id,
        reason=ReportReason.BROKEN,
        details="App crashes immediately upon launch on Android 14",
        status=ReportStatus.PENDING,
        reporter_ip_hash="abc123hash",
    )
    assert report.app_id == app_id
    assert report.reason == ReportReason.BROKEN
    assert report.status == ReportStatus.PENDING
    assert report.reporter_ip_hash == "abc123hash"
    assert report.reporter_id is None
    assert report.admin_notes is None
