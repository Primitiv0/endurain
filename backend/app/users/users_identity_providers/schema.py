"""Backward-compat shim: use auth.identity_links.schema instead."""
# noqa: F401, F403
from auth.identity_links.schema import *  # noqa: F401, F403
from auth.identity_links.schema import (
    UsersIdentityProviderBase,
    UsersIdentityProviderCreate,
    UsersIdentityProviderRead,
    UsersIdentityProviderResponse,
    UsersIdentityProviderTokenUpdate,
)  # noqa: F401
