"""Tests for profile browser redirect router."""

import profile.browser_redirect_router as profile_browser_redirect_router
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import core.config as core_config
import core.database as core_database


class TestLinkIdentityProvider:
    """Test suite for link_identity_provider endpoint."""

    endpoint = "/api/v1/profile/idp/1/link?link_token=test-token"

    def _make_app(self):
        app = FastAPI()
        app.include_router(
            profile_browser_redirect_router.router,
            prefix=core_config.ROOT_PATH + "/profile",
        )
        mock_db = MagicMock(spec=Session)
        app.dependency_overrides[core_database.get_db] = lambda: mock_db
        return app

    def test_successful_redirect(self):
        app = self._make_app()
        client = TestClient(app)

        mock_token = MagicMock(spec=["id", "idp_id", "user_id", "ip_address"])
        mock_token.id = 1
        mock_token.idp_id = 1
        mock_token.user_id = 1
        mock_token.ip_address = None

        mock_idp = MagicMock(spec=["enabled", "name"])
        mock_idp.enabled = True
        mock_idp.name = "TestIdP"

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch(
                "profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash",
                return_value=mock_token,
            ),
            patch("profile.browser_redirect_router.idp_crud.get_identity_provider", return_value=mock_idp),
            patch(
                "profile.browser_redirect_router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id",
                return_value=None,
            ),
            patch("profile.browser_redirect_router.idp_link_token_crud.mark_token_as_used", return_value=True),
            patch(
                "profile.browser_redirect_router.oauth_state_utils.create_state_id_and_nonce",
                return_value=("state-id", "nonce"),
            ),
            patch("profile.browser_redirect_router.oauth_state_crud.create_oauth_state"),
            patch(
                "profile.browser_redirect_router.idp_service.idp_service.initiate_link",
                new_callable=AsyncMock,
                return_value="https://idp.example.com/auth",
            ),
        ):
            response = client.get(self.endpoint, follow_redirects=False)

        assert response.status_code == 307, f"Expected 307, got {response.status_code}: {response.text}"
        assert response.headers["location"] == "https://idp.example.com/auth"

    def test_invalid_token(self):
        app = self._make_app()
        client = TestClient(app)

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch("profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash", return_value=None),
        ):
            response = client.get(self.endpoint)

        assert response.status_code == 401

    def test_idp_mismatch(self):
        app = self._make_app()
        client = TestClient(app)

        mock_token = MagicMock()
        mock_token.idp_id = 999

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch(
                "profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash",
                return_value=mock_token,
            ),
        ):
            response = client.get(self.endpoint)

        assert response.status_code == 401

    def test_idp_not_found(self):
        app = self._make_app()
        client = TestClient(app)

        mock_token = MagicMock()
        mock_token.idp_id = 1
        mock_token.user_id = 1

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch(
                "profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash",
                return_value=mock_token,
            ),
            patch("profile.browser_redirect_router.idp_crud.get_identity_provider", return_value=None),
        ):
            response = client.get(self.endpoint)

        assert response.status_code == 404

    def test_idp_disabled(self):
        app = self._make_app()
        client = TestClient(app)

        mock_token = MagicMock()
        mock_token.idp_id = 1
        mock_token.user_id = 1

        mock_idp = MagicMock()
        mock_idp.enabled = False

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch(
                "profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash",
                return_value=mock_token,
            ),
            patch("profile.browser_redirect_router.idp_crud.get_identity_provider", return_value=mock_idp),
        ):
            response = client.get(self.endpoint)

        assert response.status_code == 404

    def test_already_linked(self):
        app = self._make_app()
        client = TestClient(app)

        mock_token = MagicMock()
        mock_token.idp_id = 1
        mock_token.user_id = 1

        mock_idp = MagicMock()
        mock_idp.enabled = True
        mock_idp.name = "TestIdP"

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch(
                "profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash",
                return_value=mock_token,
            ),
            patch("profile.browser_redirect_router.idp_crud.get_identity_provider", return_value=mock_idp),
            patch(
                "profile.browser_redirect_router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id",
                return_value=MagicMock(),
            ),
        ):
            response = client.get(self.endpoint)

        assert response.status_code == 409

    def test_token_replay(self):
        app = self._make_app()
        client = TestClient(app)

        mock_token = MagicMock()
        mock_token.id = 1
        mock_token.idp_id = 1
        mock_token.user_id = 1

        mock_idp = MagicMock()
        mock_idp.enabled = True
        mock_idp.name = "TestIdP"

        with (
            patch(
                "profile.browser_redirect_router.idp_link_token_utils.hash_idp_link_token", return_value="hashed-token"
            ),
            patch(
                "profile.browser_redirect_router.idp_link_token_crud.get_idp_link_token_by_hash",
                return_value=mock_token,
            ),
            patch("profile.browser_redirect_router.idp_crud.get_identity_provider", return_value=mock_idp),
            patch(
                "profile.browser_redirect_router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id",
                return_value=None,
            ),
            patch("profile.browser_redirect_router.idp_link_token_crud.mark_token_as_used", return_value=False),
        ):
            response = client.get(self.endpoint)

        assert response.status_code == 400
