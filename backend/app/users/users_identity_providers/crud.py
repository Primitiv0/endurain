"""Backward-compat shim: use auth.identity_links.crud instead."""
# noqa: F401, F403
from auth.identity_links.crud import *  # noqa: F401, F403
from auth.identity_links.crud import (
    check_user_identity_providers_by_idp_id,
    get_user_identity_providers_by_user_id,
    get_user_identity_provider_by_user_id_and_idp_id,
    get_user_identity_provider_by_subject_and_idp_id,
    create_user_identity_provider,
    update_user_identity_provider_last_login,
    store_user_identity_provider_tokens,
    clear_user_identity_provider_refresh_token_by_user_id_and_idp_id,
    delete_user_identity_provider,
)  # noqa: F401
