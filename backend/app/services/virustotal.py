"""VirusTotal hash lookup integration.

Optional scanner: checks APK sha256 against VirusTotal API v3 without uploading
the full binary. If flagged, updates APK record with detection count and
surfaces clear warnings in API responses.
"""
from __future__ import annotations

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class VirusTotalResult(BaseModel):
    status: str  # "clean", "flagged", "unknown"
    positives: int = 0
    total: int = 0
    permalink: str | None = None


async def lookup_virustotal_hash(sha256: str) -> VirusTotalResult:
    """Query VirusTotal API v3 for an APK's sha256 hash."""
    api_key = settings.virustotal_api_key
    if not api_key:
        return VirusTotalResult(status="unknown")

    clean_hash = sha256.lower().strip()
    url = f"https://www.virustotal.com/api/v3/files/{clean_hash}"
    headers = {"x-apikey": api_key, "User-Agent": "AmaApp-Security/1.0"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                return VirusTotalResult(status="unknown")
            if resp.status_code != 200:
                log.warning("virustotal_api_error", status_code=resp.status_code)
                return VirusTotalResult(status="unknown")

            data = resp.json().get("data", {})
            attributes = data.get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0) + stats.get("suspicious", 0)
            undetected = stats.get("undetected", 0) + stats.get("harmless", 0)
            total = malicious + undetected

            permalink = f"https://www.virustotal.com/gui/file/{clean_hash}"
            status = "flagged" if malicious > 0 else "clean"
            return VirusTotalResult(
                status=status,
                positives=malicious,
                total=total,
                permalink=permalink,
            )
    except Exception as exc:
        log.warning("virustotal_lookup_failed", error=str(exc))
        return VirusTotalResult(status="unknown")
