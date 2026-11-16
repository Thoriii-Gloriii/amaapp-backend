"""URL moderation and security validation for Web App listings.

Guards:
1. Scheme validation: only http and https are allowed (https strongly recommended).
   Disallowed schemes (javascript:, file:, data:, ftp:, etc.) are rejected immediately.
2. Userinfo protection: user:password@host is rejected to prevent credential leaks and phishing obfuscation.
3. Blocked domain lists:
   - Reserved / local domains: localhost, *.local, *.internal, *.lan, *.test, *.example, *.invalid
   - Cloud metadata hosts: instance-data, metadata.google.internal
   - Suspicious / malware test domains and configurable blocked domain list
4. SSRF address validation:
   - Host IP or resolved DNS target must be a globally routable public unicast IP.
   - Loopback (127.0.0.0/8), RFC1918 private (10/8, 172.16/12, 192.168/16), link-local (169.254/16),
     and cloud metadata IPs are rejected.
5. Reachability check:
   - Uses PinnedSSRFTransport to safely ping the URL without DNS rebinding vulnerability.
"""
from __future__ import annotations

import ipaddress
import os
import re
import socket
import time
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.ssrf import BlockedAddressError, is_blocked_public_ip, make_ssrf_client

log = get_logger(__name__)

# Reserved or local domain suffixes that cannot be public web apps
_BLOCKED_SUFFIXES = (
    ".local",
    ".internal",
    ".lan",
    ".test",
    ".example",
    ".invalid",
    ".localhost",
)

_BLOCKED_EXACT_HOSTS = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "instance-data",
    "metadata.google.internal",
})

# Extra blocked domains from environment (comma-separated)
_EXTRA_BLOCKED_DOMAINS = frozenset(
    d.strip().lower()
    for d in os.getenv("AMAAPP_BLOCKED_DOMAINS", "").split(",")
    if d.strip()
)


class WebAppHealthResult(BaseModel):
    reachable: bool
    status_code: int | None = None
    response_time_ms: float = 0.0
    error: str | None = None
    final_url: str | None = None


def validate_web_app_url(url: str, *, allow_private: bool = False) -> str:
    """Validate a web app URL for scheme, format, userinfo, and domain blocklists.

    Raises:
        ValueError: If the URL fails any security or format checks.
    """
    clean_url = (url or "").strip()
    if not clean_url:
        raise ValueError("URL cannot be empty")

    try:
        parsed = urlparse(clean_url)
    except Exception as exc:
        raise ValueError(f"Invalid URL structure: {exc}") from exc

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Invalid scheme {scheme!r}: only http and https are allowed")

    if not parsed.netloc:
        raise ValueError("URL must include a valid hostname")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded username or password are not permitted")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("URL missing valid host")

    # Check against known blocked exact hosts
    if hostname in _BLOCKED_EXACT_HOSTS or hostname in _EXTRA_BLOCKED_DOMAINS:
        raise ValueError(f"Domain {hostname!r} is on the blocked domain list")

    # Check blocked suffixes
    for suffix in _BLOCKED_SUFFIXES:
        if hostname.endswith(suffix):
            raise ValueError(f"Domain {hostname!r} uses a reserved/local top-level domain ({suffix})")

    if not allow_private:
        # Check if the hostname is a raw IP address
        try:
            ip_obj = ipaddress.ip_address(hostname)
            if is_blocked_public_ip(ip_obj):
                raise ValueError(f"Host IP {hostname} is a private, loopback, or reserved address")
        except ValueError as err:
            # If not a literal IP, check whether it's our ValueError or just not an IP
            if "private, loopback, or reserved" in str(err):
                raise
            # Otherwise hostname is a domain name, which will be validated during DNS resolution

    return clean_url


async def check_web_app_url_health(url: str, *, timeout: float = 6.0) -> WebAppHealthResult:
    """Safely test whether a web app URL is reachable using DNS-pinned SSRF transport."""
    try:
        validated_url = validate_web_app_url(url)
    except ValueError as val_err:
        return WebAppHealthResult(
            reachable=False,
            error=str(val_err),
        )

    t0 = time.perf_counter()
    try:
        async with make_ssrf_client(
            is_blocked_public_ip,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "AmaApp-Web-Moderator/1.0 (+https://amaapp.dev)"},
        ) as client:
            # Try HEAD first; if method not allowed (405) or not implemented (501), fallback to GET
            try:
                resp = await client.head(validated_url)
                if resp.status_code in (405, 501):
                    resp = await client.get(validated_url)
            except (httpx.RequestError, httpx.HTTPStatusError):
                resp = await client.get(validated_url)

            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            is_ok = 200 <= resp.status_code < 400
            return WebAppHealthResult(
                reachable=is_ok,
                status_code=resp.status_code,
                response_time_ms=elapsed_ms,
                final_url=str(resp.url),
                error=None if is_ok else f"HTTP status {resp.status_code}",
            )
    except BlockedAddressError as blocked_err:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return WebAppHealthResult(
            reachable=False,
            response_time_ms=elapsed_ms,
            error=f"SSRF blocked: {blocked_err}",
        )
    except httpx.TimeoutException:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return WebAppHealthResult(
            reachable=False,
            response_time_ms=elapsed_ms,
            error="Connection timed out",
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return WebAppHealthResult(
            reachable=False,
            response_time_ms=elapsed_ms,
            error=f"Connection failed: {exc}",
        )
