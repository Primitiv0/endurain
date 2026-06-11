"""Additional tests for the public identity provider router (uncovered paths)."""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import auth.identity_providers.public_router as public_router


def _build_app(mock_db) -> TestClient:
    import core.database as core_db

    app = FastAPI()
    app.include_router(public_router.router, prefix="/api/v1/public/idp")
    app.dependency_overrides[core_db.get_db] = lambda: mock_db
    return TestClient(app)


class TestGetEnabledProviders:
    @patch("auth.identity_providers.public_router.idp_crud.get_enabled_providers")
    def test_success(self, mock_get, mock_db):
        client = _build_app(mock_db)
        provider = MagicMock()
        provider.id = 1
        provider.name = "Google"
        provider.slug = "google"
        provider.icon = "google-icon"
        mock_get.return_value = [provider]

        response = client.get("/api/v1/public/idp")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Google"

    @patch("auth.identity_providers.public_router.idp_crud.get_enabled_providers")
    def test_empty(self, mock_get, mock_db):
        client = _build_app(mock_db)
        mock_get.return_value = []

        response = client.get("/api/v1/public/idp")
        assert response.status_code == 200
        assert response.json() == []


class TestInitiateLoginErrors:
    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    def test_provider_not_found(self, mock_get_idp, mock_db):
        client = _build_app(mock_db)
        mock_get_idp.return_value = None

        response = client.get(
            "/api/v1/public/idp/login/unknown",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == 404

    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    def test_provider_disabled(self, mock_get_idp, mock_db):
        client = _build_app(mock_db)
        idp = MagicMock()
        idp.enabled = False
        mock_get_idp.return_value = idp

        response = client.get(
            "/api/v1/public/idp/login/disabled",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == 404

    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    @patch("auth.identity_providers.public_router.idp_utils.validate_pkce_challenge")
    @patch("auth.identity_providers.public_router.idp_utils.validate_redirect_url")
    @patch("auth.identity_providers.public_router.idp_service.idp_service.initiate_login")
    def test_generic_exception(self, mock_login, mock_val_url, mock_val_pkce, mock_get_idp, mock_db):
        client = _build_app(mock_db)
        idp = MagicMock()
        idp.enabled = True
        idp.slug = "test"
        idp.id = 1
        mock_get_idp.return_value = idp
        mock_login.side_effect = Exception("Unexpected error")

        response = client.get(
            "/api/v1/public/idp/login/test",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
        )
        assert response.status_code == 500

    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    @patch("auth.identity_providers.public_router.idp_utils.validate_pkce_challenge")
    @patch("auth.identity_providers.public_router.idp_utils.validate_redirect_url")
    @patch("auth.identity_providers.public_router.idp_service.idp_service.initiate_login")
    @patch("auth.identity_providers.public_router.idp_utils.is_custom_scheme_redirect")
    @patch("auth.identity_providers.public_router.oauth_state_crud.create_oauth_state")
    def test_invalid_client_type_defaults_to_web(
        self,
        mock_create_state,
        mock_custom_scheme,
        mock_login,
        mock_val_url,
        mock_val_pkce,
        mock_get_idp,
        mock_db,
    ):
        client = _build_app(mock_db)
        idp = MagicMock()
        idp.enabled = True
        idp.slug = "test"
        idp.id = 1
        mock_get_idp.return_value = idp
        mock_custom_scheme.return_value = False
        mock_login.return_value = "https://provider.example/auth"

        response = client.get(
            "/api/v1/public/idp/login/test",
            params={
                "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
                "code_challenge_method": "S256",
            },
            headers={"X-Client-Type": "desktop"},
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert mock_create_state.call_args.kwargs["client_type"] == "web"


class TestHandleCallback:
    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    def test_provider_not_found(self, mock_get_idp, mock_db):
        client = _build_app(mock_db)
        mock_get_idp.return_value = None

        response = client.get(
            "/api/v1/public/idp/callback/test?code=abc&state=xyz",
            follow_redirects=False,
        )
        assert response.status_code == 404

    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    @patch("auth.identity_providers.public_router.oauth_state_crud.get_oauth_state_by_id_and_not_used")
    def test_oauth_state_not_found(self, mock_get_state, mock_get_idp, mock_db):
        client = _build_app(mock_db)
        idp = MagicMock()
        idp.enabled = True
        idp.name = "Test"
        mock_get_idp.return_value = idp
        mock_get_state.return_value = None

        response = client.get(
            "/api/v1/public/idp/callback/test?code=abc&state=invalid",
            follow_redirects=False,
        )
        assert response.status_code == 400

    @patch("auth.identity_providers.public_router.idp_crud.get_identity_provider_by_slug")
    @patch("auth.identity_providers.public_router.oauth_state_crud.get_oauth_state_by_id_and_not_used")
    @patch("auth.identity_providers.public_router.oauth_state_crud.mark_oauth_state_used")
    def test_state_replay(self, mock_mark_used, mock_get_state, mock_get_idp, mock_db):
        client = _build_app(mock_db)
        idp = MagicMock()
        idp.enabled = True
        idp.name = "Test"
        idp.slug = "test"
        mock_get_idp.return_value = idp
        oauth_state = MagicMock()
        oauth_state.client_type = "web"
        mock_get_state.return_value = oauth_state
        mock_mark_used.return_value = False

        response = client.get(
            "/api/v1/public/idp/callback/test?code=abc&state=replayed",
            follow_redirects=False,
        )
        assert response.status_code == 400


class TestTokenExchange:
    @patch("auth.identity_providers.public_router.users_session_crud.get_session_with_oauth_state")
    def test_session_not_found(self, mock_get_session, mock_db):
        client = _build_app(mock_db)
        mock_get_session.return_value = None

        response = client.post(
            "/api/v1/public/idp/session/unknown/tokens",
            json={"code_verifier": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"},
        )
        assert response.status_code == 404
