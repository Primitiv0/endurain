"""Network helpers shared across the application.

Currently provides proxy-aware client IP extraction
and SSRF guards for outbound HTTP calls. Lives in
``core/`` so any module — including other ``core/``
modules such as rate limiting — can use it without
creating a dependency on the ``users`` package.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

import core.config as core_config


def _is_trusted_peer(peer_ip: str) -> bool:
    """Check whether ``peer_ip`` is in the TRUSTED_PROXIES allow-list.

    Supports exact IPs and CIDR notation. The special value ``"*"``
    (the default) trusts every peer.

    Args:
        peer_ip: The direct TCP-connection IP of the caller.

    Returns:
        True if the peer is trusted, False otherwise.
    """
    trusted = core_config.settings.TRUSTED_PROXIES
    if trusted == ["*"]:
        return True
    try:
        addr = ipaddress.ip_address(peer_ip)
        for entry in trusted:
            entry = entry.strip()
            if not entry:
                continue
            try:
                network = ipaddress.ip_network(entry, strict=False)
                if addr in network:
                    return True
            except ValueError:
                # Entry is not a valid network — compare as plain string
                if peer_ip == entry:
                    return True
    except ValueError:
        pass
    return False


def get_ip_address(request: Request) -> str:
    """
    Extract client IP address from request, respecting TRUSTED_PROXIES.

    Proxy headers (``X-Forwarded-For``, ``X-Real-IP``) are only trusted
    when the direct TCP peer matches an entry in ``TRUSTED_PROXIES``.
    This prevents attackers from spoofing their IP by injecting those
    headers on direct connections.

    When ``TRUSTED_PROXIES`` is ``["*"]`` (the default) all peers are
    trusted.

    Args:
        request: Request object with headers and client info.

    Returns:
        Client IP address or "unknown" if indeterminate.
    """
    peer_ip = request.client.host if request.client else None

    if peer_ip and _is_trusted_peer(peer_ip):
        # Peer is a trusted proxy — honour the forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the leftmost IP: the original client
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

    # Untrusted peer or no peer info — use the raw socket IP
    return peer_ip or "unknown"


# Schemes the application is willing to dial. Anything
# else (file://, gopher://, ftp://, data://, javascript:)
# is rejected outright.
_ALLOWED_OUTBOUND_SCHEMES: frozenset[str] = frozenset({"http", "https"})


def _is_private_or_reserved(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    """Return True if ``addr`` belongs to any non-routable range.

    Combines every "do not dial" predicate Python's
    ``ipaddress`` module exposes: private (RFC1918,
    fc00::/7), loopback, link-local, multicast,
    unspecified (0.0.0.0, ::), and reserved blocks. Any
    of these would let an attacker pivot to internal
    infrastructure or cloud metadata services.
    """
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
        or addr.is_reserved
    )


def reject_private_url(url: str) -> None:
    """Refuse to dial URLs that resolve to private/internal hosts.

    Mitigates Server-Side Request Forgery (SSRF) by
    enforcing two checks before any outbound HTTP call:

    1. The scheme must be ``http`` or ``https``.
    2. Every address the hostname resolves to (both A
       and AAAA records) must be a public unicast
       address. A single private/loopback/link-local
       answer aborts the request — this defends against
       DNS rebinding where an attacker-controlled host
       returns a public IP on the first lookup and a
       private IP on the next.

    Note: this is a *time-of-check* guard. Callers that
    want full TOCTOU safety should also pin the resolved
    public IP and dial it directly with the original
    Host header. For our current use cases (admin-set
    OIDC discovery / JWKS endpoints) the time-of-check
    guard is sufficient hardening.

    Args:
        url: The fully-qualified URL the caller intends
            to fetch.

    Raises:
        HTTPException: 400 if the URL is malformed,
            uses a forbidden scheme, has no hostname,
            or resolves to any non-public address.
    """
    try:
        parsed = urlparse(url)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed URL",
        ) from err

    if parsed.scheme.lower() not in _ALLOWED_OUTBOUND_SCHEMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL scheme is not permitted",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL has no hostname",
        )

    # Resolve every A/AAAA record and require that all
    # of them be public. ``getaddrinfo`` returns a list
    # of ``(family, type, proto, canonname, sockaddr)``
    # tuples; ``sockaddr[0]`` is the textual IP.
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL hostname could not be resolved",
        ) from err

    for info in infos:
        sockaddr = info[4]
        ip_text = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip_text)
        except ValueError:
            # Defensive: if the resolver hands back
            # something we can't parse, treat as unsafe.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL resolves to an unparseable address",
            )
        if _is_private_or_reserved(addr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL resolves to a non-public address",
            )
