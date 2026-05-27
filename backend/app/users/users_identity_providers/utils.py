"""Backward-compat shim: use auth.identity_links.utils instead."""
# noqa: F401, F403
from auth.identity_links.utils import *  # noqa: F401, F403
from auth.identity_links.utils import (
    get_user_identity_provider_refresh_token_by_user_id_and_idp_id,
    enrich_user_identity_providers,
)  # noqa: F401
