"""Tests for auth.identity_links.utils module."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from auth.identity_links import utils as identity_links_utils
from auth.identity_links.schema import UsersIdentityProviderResponse


class TestGetUserIdentityProviderRefreshToken:
    """Tests for get_user_identity_provider_refresh_token_by_user_id_and_idp_id."""

    def test_returns_refresh_token_when_link_exists(self, mock_db):
        """
        Returns encrypted refresh token from the link.

        Args:
            mock_db: Mocked database session.

        Asserts:
            - Returns idp_refresh_token from the found link.
        """
        mock_link = MagicMock()
        mock_link.idp_refresh_token = "encrypted-token-abc"

        with patch(
            "auth.identity_links.utils.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id",
            return_value=mock_link,
        ):
            result = identity_links_utils.get_user_identity_provider_refresh_token_by_user_id_and_idp_id(
                user_id=1,
                idp_id=2,
                db=mock_db,
            )

        assert result == "encrypted-token-abc"

    def test_returns_none_when_link_not_found(self, mock_db):
        """
        Returns None when no link exists for user + IdP.

        Args:
            mock_db: Mocked database session.

        Asserts:
            - Returns None.
        """
        with patch(
            "auth.identity_links.utils.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id",
            return_value=None,
        ):
            result = identity_links_utils.get_user_identity_provider_refresh_token_by_user_id_and_idp_id(
                user_id=1,
                idp_id=2,
                db=mock_db,
            )

        assert result is None


class TestEnrichUserIdentityProviders:
    """Tests for enrich_user_identity_providers."""

    def test_returns_empty_list_for_empty_input(self, mock_db):
        """
        Returns empty list immediately without DB queries.

        Args:
            mock_db: Mocked database session.

        Asserts:
            - Returns empty list.
            - No db.execute called.
        """
        result = identity_links_utils.enrich_user_identity_providers([], 1, mock_db)

        assert result == []
        mock_db.execute.assert_not_called()

    def test_enriches_links_with_idp_details(self, mock_db):
        """
        Enriches links with name, slug, icon, provider_type.

        Args:
            mock_db: Mocked database session.

        Asserts:
            - Returns enriched UsersIdentityProviderResponse list.
            - idp_crud called once for batch fetch.
        """
        now = datetime.now(UTC)

        mock_link = MagicMock()
        mock_link.id = 1
        mock_link.user_id = 1
        mock_link.idp_id = 1
        mock_link.idp_subject = "sub-123"
        mock_link.linked_at = now
        mock_link.last_login = now
        mock_link.idp_access_token_expires_at = None
        mock_link.idp_refresh_token_updated_at = None

        mock_idp = MagicMock()
        mock_idp.id = 1
        mock_idp.name = "TestIdP"
        mock_idp.slug = "test-idp"
        mock_idp.icon = "https://example.com/icon.svg"
        mock_idp.provider_type = "oidc"

        with patch(
            "auth.identity_links.utils.idp_crud.get_identity_providers_by_ids",
            return_value=[mock_idp],
        ) as mock_get_idps:
            result = identity_links_utils.enrich_user_identity_providers([mock_link], 1, mock_db)

        assert len(result) == 1
        assert isinstance(result[0], UsersIdentityProviderResponse)
        assert result[0].idp_name == "TestIdP"
        assert result[0].idp_slug == "test-idp"
        assert result[0].idp_icon == "https://example.com/icon.svg"
        assert result[0].idp_provider_type == "oidc"
        mock_get_idps.assert_called_once_with([1], mock_db)

    def test_skips_link_when_idp_not_found(self, mock_db):
        """
        Skips and logs warning when IdP missing from batch fetch.

        Args:
            mock_db: Mocked database session.

        Asserts:
            - Returns empty list when IdP not in map.
        """
        now = datetime.now(UTC)

        mock_link = MagicMock()
        mock_link.id = 1
        mock_link.user_id = 1
        mock_link.idp_id = 99
        mock_link.idp_subject = "sub-xyz"
        mock_link.linked_at = now
        mock_link.last_login = None
        mock_link.idp_access_token_expires_at = None
        mock_link.idp_refresh_token_updated_at = None

        with patch(
            "auth.identity_links.utils.idp_crud.get_identity_providers_by_ids",
            return_value=[],
        ):
            result = identity_links_utils.enrich_user_identity_providers([mock_link], 1, mock_db)

        assert result == []

    def test_batch_fetches_all_idps_in_one_query(self, mock_db):
        """
        Uses a single batch query for all IdP IDs.

        Args:
            mock_db: Mocked database session.

        Asserts:
            - get_identity_providers_by_ids called once with all IDs.
        """
        now = datetime.now(UTC)

        mock_links = []
        for i in range(1, 4):
            link = MagicMock()
            link.id = i
            link.user_id = 1
            link.idp_id = i
            link.idp_subject = f"sub-{i}"
            link.linked_at = now
            link.last_login = None
            link.idp_access_token_expires_at = None
            link.idp_refresh_token_updated_at = None
            mock_links.append(link)

        mock_idps = []
        for i in range(1, 4):
            idp = MagicMock()
            idp.id = i
            idp.name = f"IdP {i}"
            idp.slug = f"idp-{i}"
            idp.icon = None
            idp.provider_type = "oidc"
            mock_idps.append(idp)

        with patch(
            "auth.identity_links.utils.idp_crud.get_identity_providers_by_ids",
            return_value=mock_idps,
        ) as mock_get_idps:
            result = identity_links_utils.enrich_user_identity_providers(mock_links, 1, mock_db)

        assert len(result) == 3
        mock_get_idps.assert_called_once_with([1, 2, 3], mock_db)


class TestIdentityServiceLinkDelegation:
    """Tests for IdentityService link/unlink delegation methods."""

    def test_link_external_identity_delegates_to_crud(self):
        """
        link_external_identity delegates to crud.create_user_identity_provider.

        Asserts:
            - crud create called with correct args.
        """
        from auth.identity_service import DefaultIdentityService

        mock_db = MagicMock()
        mock_token_manager = MagicMock()
        mock_password_hasher = MagicMock()
        service = DefaultIdentityService(
            db=mock_db,
            token_manager=mock_token_manager,
            password_hasher=mock_password_hasher,
        )

        with patch("auth.identity_service.auth_identity_links_crud.create_user_identity_provider") as mock_create:
            service.link_external_identity(
                user_id=1,
                idp_id=2,
                idp_subject="sub-abc",
            )

        mock_create.assert_called_once_with(1, 2, "sub-abc", mock_db)

    def test_unlink_external_identity_delegates_to_crud(self):
        """
        unlink_external_identity delegates to crud.delete_user_identity_provider.

        Asserts:
            - crud delete called with correct args.
        """
        from auth.identity_service import DefaultIdentityService

        mock_db = MagicMock()
        mock_token_manager = MagicMock()
        mock_password_hasher = MagicMock()
        service = DefaultIdentityService(
            db=mock_db,
            token_manager=mock_token_manager,
            password_hasher=mock_password_hasher,
        )

        with patch(
            "auth.identity_service.auth_identity_links_crud.delete_user_identity_provider",
            return_value=True,
        ) as mock_delete:
            service.unlink_external_identity(
                user_id=1,
                idp_id=2,
            )

        mock_delete.assert_called_once_with(1, 2, mock_db)

    def test_unlink_external_identity_raises_404_when_not_found(self):
        """
        unlink_external_identity raises 404 when link not found.

        Asserts:
            - HTTPException with status 404 raised.
        """
        from fastapi import HTTPException

        from auth.identity_service import DefaultIdentityService

        mock_db = MagicMock()
        service = DefaultIdentityService(
            db=mock_db,
            token_manager=MagicMock(),
            password_hasher=MagicMock(),
        )

        with (
            patch(
                "auth.identity_service.auth_identity_links_crud.delete_user_identity_provider",
                return_value=False,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            service.unlink_external_identity(
                user_id=1,
                idp_id=99,
            )

        assert exc_info.value.status_code == 404
