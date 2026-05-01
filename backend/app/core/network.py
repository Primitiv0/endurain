"""Network helpers shared across the application.

Currently provides proxy-aware client IP extraction.
Lives in ``core/`` so any module — including other
``core/`` modules such as rate limiting — can use it
without creating a dependency on the ``users`` package.
"""

import ipaddress

from fastapi import Request

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
