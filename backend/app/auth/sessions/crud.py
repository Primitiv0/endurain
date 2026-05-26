"""Deprecated shim for session CRUD.

Temporary Phase 3 shim for boundary migration PR.
Canonical implementation remains in users.users_sessions.crud
until Phase 4 import burn-down.
"""

from users.users_sessions.crud import *
