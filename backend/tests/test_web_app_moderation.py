"""Tests for AmaApp Web App moderation:
- URL validation and scheme restrictions (https/http only)
- Userinfo rejection (no user:pass@host)
- Localhost, RFC1918, link-local, and metadata IP rejection
- Reserved/local domain rejection (*.local, *.internal, localhost, etc.)
- WebAppHealthResult and health check integration
"""
from __future__ import annotations

import pytest

from app.schemas.app import WebAppRejectPayload
from app.services.url_moderation import (
    WebAppHealthResult,
    check_web_app_url_health,
    validate_web_app_url,
)


def test_valid_web_app_urls() -> None:
    assert validate_web_app_url("https://mycoolapp.com") == "https://mycoolapp.com"
    assert (
        validate_web_app_url("https://github.io/myorg/project")
        == "https://github.io/myorg/project"
    )
    assert validate_web_app_url("http://open-source-app.org") == "http://open-source-app.org"


def test_reject_empty_or_malformed_url() -> None:
    with pytest.raises(ValueError, match="URL cannot be empty"):
        validate_web_app_url("")

    with pytest.raises(ValueError, match="URL must include a valid hostname"):
        validate_web_app_url("https://")


def test_reject_dangerous_schemes() -> None:
    for bad_scheme in (
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
        "ftp://files.example.com",
    ):
        with pytest.raises(ValueError, match="only http and https are allowed"):
            validate_web_app_url(bad_scheme)


def test_reject_userinfo_credentials() -> None:
    with pytest.raises(ValueError, match="embedded username or password"):
        validate_web_app_url("https://admin:secret123@legit-site.com")


def test_reject_local_and_private_addresses() -> None:
    blocked_urls = [
        "http://localhost:8000/app",
        "http://127.0.0.1:3000",
        "http://192.168.1.100",
        "http://10.0.0.5",
        "http://172.16.0.1",
        "http://169.254.169.254/latest/meta-data",
        "https://app.local",
        "https://service.internal",
        "https://instance-data",
    ]
    for url in blocked_urls:
        with pytest.raises(ValueError):
            validate_web_app_url(url)


@pytest.mark.asyncio
async def test_health_check_returns_clean_result_on_blocked_url() -> None:
    result = await check_web_app_url_health("http://localhost:9999/malicious")
    assert isinstance(result, WebAppHealthResult)
    assert result.reachable is False
    assert result.error is not None
    assert "blocked" in result.error.lower() or "reserved" in result.error.lower() or "localhost" in result.error.lower()


def test_web_app_reject_payload_schema() -> None:
    payload = WebAppRejectPayload(reason="Contains copyright infringement")
    assert payload.reason == "Contains copyright infringement"

    default_payload = WebAppRejectPayload()
    assert default_payload.reason == "Rejected by administrator"
