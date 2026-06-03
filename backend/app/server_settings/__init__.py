"""
Server settings module for configuration and database management.

This module provides server-wide configuration management, including
measurement units, currency settings, signup policies, SSO configuration,
and map tile server settings.

Exports:
    - CRUD operations: get_server_settings, edit_server_settings
    - Schemas: ServerSettings, ServerSettingsEdit, ServerSettingsRead,
      ServerSettingsReadPublic
    - Utilities: get_server_settings_or_404 (wrapper), get_tile_maps_templates
    - Models: ServerSettings (ORM model)
    - Enums: Units, Currency, PasswordType
"""

from .crud import edit_server_settings
from .crud import get_server_settings as get_server_settings_db
from .models import ServerSettings as ServerSettingsModel
from .schema import (
    Currency,
    PasswordType,
    ServerSettings,
    ServerSettingsBase,
    ServerSettingsEdit,
    ServerSettingsRead,
    ServerSettingsReadPublic,
    TileMapsTemplate,
    Units,
)
from .utils import get_server_settings_or_404, get_tile_maps_templates

__all__ = [
    "Currency",
    "PasswordType",
    # Pydantic schemas
    "ServerSettings",
    "ServerSettingsBase",
    "ServerSettingsEdit",
    # Database model
    "ServerSettingsModel",
    "ServerSettingsRead",
    "ServerSettingsReadPublic",
    "TileMapsTemplate",
    # Enums
    "Units",
    "edit_server_settings",
    # CRUD operations
    "get_server_settings_db",
    # Utility functions
    "get_server_settings_or_404",
    "get_tile_maps_templates",
]
