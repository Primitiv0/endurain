"""Backward-compat shim: use auth.identity_links.models instead."""
# noqa: F401, F403
from auth.identity_links.models import *  # noqa: F401, F403
from auth.identity_links.models import (
    UsersIdentityProvider,
)  # noqa: F401
