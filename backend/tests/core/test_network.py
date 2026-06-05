"""Tests for core.network module."""

import ipaddress
import socket
from unittest.mock import MagicMock, patch

import core.network as core_network
import pytest
from fastapi import HTTPException, Request


class TestIsTrustedPeer:
    """Tests for _is_trusted_peer function."""

    def test_wildcard_trusts_all(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["*"]):
            assert core_network._is_trusted_peer("192.168.1.1") is True
            assert core_network._is_trusted_peer("10.0.0.1") is True

    def test_exact_ip_match(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["192.168.1.1"]):
            assert core_network._is_trusted_peer("192.168.1.1") is True

    def test_exact_ip_no_match(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.1"]):
            assert core_network._is_trusted_peer("192.168.1.1") is False

    def test_cidr_match(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            assert core_network._is_trusted_peer("10.0.0.1") is True
            assert core_network._is_trusted_peer("10.255.255.255") is True

    def test_cidr_no_match(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            assert core_network._is_trusted_peer("192.168.1.1") is False

    def test_empty_trusted_proxies(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", []):
            assert core_network._is_trusted_peer("10.0.0.1") is False

    def test_invalid_peer_ip(self):
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            assert core_network._is_trusted_peer("not-an-ip") is False


class TestGetIpAddress:
    """Tests for get_ip_address function."""

    def test_no_client_returns_unknown(self):
        request = MagicMock(spec=Request)
        request.client = None
        result = core_network.get_ip_address(request)
        assert result == "unknown"

    def test_untrusted_peer_uses_direct_ip(self):
        request = MagicMock(spec=Request)
        request.client.host = "203.0.113.5"
        request.headers = {"X-Forwarded-For": "1.2.3.4"}
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            result = core_network.get_ip_address(request)
            assert result == "203.0.113.5"

    def test_trusted_proxy_x_forwarded_for(self):
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "1.2.3.4, 10.0.0.1"}
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            result = core_network.get_ip_address(request)
            assert result == "1.2.3.4"

    def test_trusted_proxy_x_real_ip(self):
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"
        request.headers = {"X-Real-IP": "5.6.7.8"}
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            result = core_network.get_ip_address(request)
            assert result == "5.6.7.8"

    def test_trusted_proxy_prefers_x_forwarded_for(self):
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "1.2.3.4", "X-Real-IP": "5.6.7.8"}
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["*"]):
            result = core_network.get_ip_address(request)
            assert result == "1.2.3.4"

    def test_trusted_proxy_no_headers_returns_direct_ip(self):
        request = MagicMock(spec=Request)
        request.client.host = "10.0.0.1"
        request.headers = {}
        with patch.object(core_network.core_config.settings, "TRUSTED_PROXIES", ["10.0.0.0/8"]):
            result = core_network.get_ip_address(request)
            assert result == "10.0.0.1"


class TestIsPrivateOrReserved:
    """Tests for _is_private_or_reserved function."""

    def test_private_ip(self):
        addr = ipaddress.ip_address("10.0.0.1")
        assert core_network._is_private_or_reserved(addr) is True

    def test_loopback(self):
        addr = ipaddress.ip_address("127.0.0.1")
        assert core_network._is_private_or_reserved(addr) is True

    def test_public_ip(self):
        addr = ipaddress.ip_address("8.8.8.8")
        assert core_network._is_private_or_reserved(addr) is False

    def test_link_local(self):
        addr = ipaddress.ip_address("169.254.1.1")
        assert core_network._is_private_or_reserved(addr) is True

    def test_multicast(self):
        addr = ipaddress.ip_address("224.0.0.1")
        assert core_network._is_private_or_reserved(addr) is True

    def test_unspecified(self):
        addr = ipaddress.ip_address("0.0.0.0")  # noqa: S104
        assert core_network._is_private_or_reserved(addr) is True

    def test_ipv6_private(self):
        addr = ipaddress.ip_address("fc00::1")
        assert core_network._is_private_or_reserved(addr) is True

    def test_ipv6_loopback(self):
        addr = ipaddress.ip_address("::1")
        assert core_network._is_private_or_reserved(addr) is True


class TestLoadSsrfAllowlist:
    """Tests for _load_ssrf_allowlist function."""

    def test_hostname_entries(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["example.com", "test.example.org"]):
            hosts, networks = core_network._load_ssrf_allowlist()
            assert "example.com" in hosts
            assert "test.example.org" in hosts
            assert not networks

    def test_cidr_entries(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["10.0.0.0/8", "192.168.0.0/16"]):
            hosts, networks = core_network._load_ssrf_allowlist()
            assert not hosts
            assert len(networks) == 2

    def test_mixed_entries(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["example.com", "10.0.0.0/8"]):
            hosts, networks = core_network._load_ssrf_allowlist()
            assert "example.com" in hosts
            assert len(networks) == 1

    def test_empty_allowlist(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", []):
            hosts, networks = core_network._load_ssrf_allowlist()
            assert not hosts
            assert not networks


class TestIsSsrfAllowlisted:
    """Tests for _is_ssrf_allowlisted function."""

    def test_hostname_match(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["internal.example.com"]):
            assert core_network._is_ssrf_allowlisted("internal.example.com", ipaddress.ip_address("10.0.0.1")) is True

    def test_hostname_case_insensitive(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["Internal.Example.Com"]):
            assert core_network._is_ssrf_allowlisted("internal.example.com", ipaddress.ip_address("10.0.0.1")) is True

    def test_network_match(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["10.0.0.0/8"]):
            assert core_network._is_ssrf_allowlisted("anyhost", ipaddress.ip_address("10.10.10.10")) is True

    def test_no_match(self):
        with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["example.com"]):
            assert core_network._is_ssrf_allowlisted("other.com", ipaddress.ip_address("10.0.0.1")) is False


class TestRejectPrivateUrl:
    """Tests for reject_private_url function."""

    def test_bad_scheme_raises(self):
        with pytest.raises(HTTPException) as exc:
            core_network.reject_private_url("file:///etc/passwd")
        assert exc.value.status_code == 400
        assert "scheme" in exc.value.detail.lower()

    def test_malformed_url_raises(self):
        with pytest.raises(HTTPException) as exc:
            core_network.reject_private_url(":::not-a-url:::")
        assert exc.value.status_code == 400

    def test_no_hostname_raises(self):
        with pytest.raises(HTTPException) as exc:
            core_network.reject_private_url("http:///path")
        assert exc.value.status_code == 400
        assert "hostname" in exc.value.detail.lower()

    def test_unresolvable_hostname_raises(self):
        with patch("core.network.socket.getaddrinfo") as mock_gai:
            mock_gai.side_effect = socket.gaierror("Name or service not known")
            with pytest.raises(HTTPException) as exc:
                core_network.reject_private_url("http://nonexistent.example.com")
            assert exc.value.status_code == 400
            assert "resolve" in exc.value.detail.lower()

    def test_unparseable_address_raises(self):
        with patch("core.network.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("not-an-ip", 0))]
            with pytest.raises(HTTPException) as exc:
                core_network.reject_private_url("http://example.com")
            assert exc.value.status_code == 400
            assert "unparseable" in exc.value.detail.lower()

    def test_private_ip_ssrf_raises(self):
        with patch("core.network.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.1", 0))]
            with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", []):
                with pytest.raises(HTTPException) as exc:
                    core_network.reject_private_url("http://internal.example.com")
                assert exc.value.status_code == 400
                assert "non-public" in exc.value.detail.lower()

    def test_private_ip_allowlisted_ok(self):
        with patch("core.network.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.1", 0))]
            with patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["10.0.0.0/8"]):
                core_network.reject_private_url("http://internal.example.com")

    def test_public_ip_success(self):
        with patch("core.network.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("8.8.8.8", 0))]
            core_network.reject_private_url("http://google.com")

    def test_allowlisted_private_url_logs(self):
        with (
            patch("core.network.socket.getaddrinfo") as mock_gai,
            patch.object(core_network.core_config.settings, "SSRF_ALLOWED_HOSTS", ["10.0.0.0/8"]),
            patch.object(core_network.core_logger, "print_to_log") as mock_log,
        ):
            mock_gai.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.1", 0))]
            core_network.reject_private_url("http://internal.example.com", purpose="test")
            mock_log.assert_called_once()
            assert "SSRF allowlist hit" in mock_log.call_args[0][0]
