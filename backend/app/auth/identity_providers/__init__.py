"""
Identity providers module for SSO/OAuth authentication.

This module provides configuration and OAuth2/OIDC flows for external
identity providers (e.g., Keycloak, Authentik, Authelia, Pocket ID,
Casdoor), including PKCE-protected login, token exchange, ID token
verification via JWKS, and admin CRUD for provider configuration.

Exports:
    - CRUD: get_identity_provider, get_identity_provider_by_slug,
      get_all_identity_providers, get_identity_providers_by_ids,
      get_enabled_providers, create_identity_provider,
      update_identity_provider, delete_identity_provider
    - Schemas: IdentityProvider, IdentityProviderBase,
      IdentityProviderCreate, IdentityProviderUpdate,
      IdentityProviderPublic, IdentityProviderTemplate,
      TokenExchangeRequest, TokenExchangeResponse
    - Models: IdentityProvider (ORM model)
    - Service: idp_service, IdentityProviderService, TokenAction
    - Utils: validate_redirect_url, validate_pkce_challenge,
      validate_pkce_verifier, get_idp_templates, get_idp_template,
      refresh_idp_tokens_if_needed, clear_all_idp_tokens
"""

from .crud import (
    create_identity_provider,
    delete_identity_provider,
    get_all_identity_providers,
    get_enabled_providers,
    get_identity_provider,
    get_identity_provider_by_slug,
    get_identity_providers_by_ids,
    update_identity_provider,
)
from .models import IdentityProvider as IdentityProviderModel
from .schema import (
    IdentityProvider,
    IdentityProviderBase,
    IdentityProviderCreate,
    IdentityProviderPublic,
    IdentityProviderTemplate,
    IdentityProviderUpdate,
    TokenExchangeRequest,
    TokenExchangeResponse,
)
from .service import IdentityProviderService, TokenAction, idp_service
from .utils import (
    clear_all_idp_tokens,
    get_idp_template,
    get_idp_templates,
    refresh_idp_tokens_if_needed,
    validate_pkce_challenge,
    validate_pkce_verifier,
    validate_redirect_url,
)

__all__ = [
    # CRUD operations
    "get_identity_provider",
    "get_identity_provider_by_slug",
    "get_all_identity_providers",
    "get_identity_providers_by_ids",
    "get_enabled_providers",
    "create_identity_provider",
    "update_identity_provider",
    "delete_identity_provider",
    # Database model
    "IdentityProviderModel",
    # Pydantic schemas
    "IdentityProvider",
    "IdentityProviderBase",
    "IdentityProviderCreate",
    "IdentityProviderUpdate",
    "IdentityProviderPublic",
    "IdentityProviderTemplate",
    "TokenExchangeRequest",
    "TokenExchangeResponse",
    # Service layer
    "IdentityProviderService",
    "TokenAction",
    "idp_service",
    # Utilities
    "validate_redirect_url",
    "validate_pkce_challenge",
    "validate_pkce_verifier",
    "get_idp_templates",
    "get_idp_template",
    "refresh_idp_tokens_if_needed",
    "clear_all_idp_tokens",
]
