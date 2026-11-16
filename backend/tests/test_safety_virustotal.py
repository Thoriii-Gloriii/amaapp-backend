"""Tests for AmaApp safety and VirusTotal integration:
- VirusTotalResult model
- lookup_virustotal_hash graceful fallback when no API key configured
- Clear 'flagged by VirusTotal' warning integration in ApkRead
- Combined safety warning generation (debug build, unreviewed, malware detection)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.apk import ApkStatus
from app.schemas.app import ApkRead
from app.services.virustotal import VirusTotalResult, lookup_virustotal_hash


@pytest.mark.asyncio
async def test_virustotal_fallback_when_no_key() -> None:
    # When no VIRUSTOTAL_API_KEY is configured, lookup returns unknown status without failing
    res = await lookup_virustotal_hash("a" * 64)
    assert isinstance(res, VirusTotalResult)
    assert res.status == "unknown"
    assert res.positives == 0


def test_apk_read_virustotal_warning() -> None:
    now = datetime.now(timezone.utc)

    # 1. Flagged build with 4 positive detections
    apk_flagged = ApkRead(
        id=uuid.uuid4(),
        app_id=uuid.uuid4(),
        file_name="malware-suspect.apk",
        size_bytes=1024,
        sha256="f" * 64,
        version_code=1,
        version_name="1.0",
        min_sdk=24,
        target_sdk=34,
        signer_sha256="s" * 64,
        permissions=[],
        native_code=[],
        status=ApkStatus.PUBLISHED,
        rejection_reason=None,
        published_at=now,
        created_at=now,
        is_debug_build=False,
        vt_status="flagged",
        vt_positives=4,
        vt_total=72,
        vt_permalink="https://www.virustotal.com/gui/file/" + ("f" * 64),
    )
    assert "flagged by VirusTotal (4/72)" in (apk_flagged.warning or "")

    # 2. Combined: debug build + unreviewed + flagged by VirusTotal
    apk_combined = ApkRead(
        id=uuid.uuid4(),
        app_id=uuid.uuid4(),
        file_name="bad-debug.apk",
        size_bytes=1024,
        sha256="e" * 64,
        version_code=2,
        version_name="2.0-debug",
        min_sdk=24,
        target_sdk=34,
        signer_sha256="s" * 64,
        permissions=[],
        native_code=[],
        status=ApkStatus.PENDING_REVIEW,
        rejection_reason=None,
        published_at=None,
        created_at=now,
        is_debug_build=True,
        vt_status="flagged",
        vt_positives=7,
        vt_total=70,
    )
    assert apk_combined.warning == "debug build, unreviewed, flagged by VirusTotal (7/70)"

    # 3. Clean published release build: no warning
    apk_clean = ApkRead(
        id=uuid.uuid4(),
        app_id=uuid.uuid4(),
        file_name="clean-release.apk",
        size_bytes=1024,
        sha256="c" * 64,
        version_code=3,
        version_name="3.0",
        min_sdk=24,
        target_sdk=34,
        signer_sha256="s" * 64,
        permissions=[],
        native_code=[],
        status=ApkStatus.PUBLISHED,
        rejection_reason=None,
        published_at=now,
        created_at=now,
        is_debug_build=False,
        vt_status="clean",
        vt_positives=0,
        vt_total=72,
    )
    assert apk_clean.warning is None
