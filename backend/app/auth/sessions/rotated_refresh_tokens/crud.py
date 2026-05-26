"""Deprecated shim for rotated token CRUD.

Temporary Phase 3 shim for boundary migration PR.
Canonical implementation remains in
users.users_sessions.rotated_refresh_tokens.crud until
Phase 4 import burn-down.
"""

from users.users_sessions.rotated_refresh_tokens.crud import *
