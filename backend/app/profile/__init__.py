"""
Profile module for user profile management and operations.

This module provides functionality for:
- User profile retrieval and updates
- MFA (Multi-Factor Authentication) setup and management
- Profile data export and import (ZIP archives)
- Identity provider linking and management
- Session management

Exports:
    - Schemas: MFARequest, MFASetupRequest, MFASetupResponse,
      MFAStatusResponse
    - MFA Store: MFASecretStore
    - Services: ExportService, ImportService
    - Exceptions: ProfileOperationError, ExportError, ProfileImportError,
      and related exception classes
    - Utils: setup_user_mfa, enable_user_mfa, disable_user_mfa,
      verify_user_mfa, is_mfa_enabled_for_user
"""

from .exceptions import (
    ActivityLimitError,
    DatabaseConnectionError,
    DataCollectionError,
    DataIntegrityError,
    DiskSpaceError,
    ExportError,
    ExportTimeoutError,
    FileFormatError,
    FileSizeError,
    FileSystemError,
    ImportTimeoutError,
    ImportValidationError,
    JSONParseError,
    MemoryAllocationError,
    ProfileImportError,
    ProfileOperationError,
    SchemaValidationError,
    ZipCreationError,
    ZipStructureError,
)
from .export_service import ExportService
from .import_service import ImportService
from .mfa_store import MFASecretStore, RedisMFASecretStore
from .schema import (
    MFARequest,
    MFASetupRequest,
    MFASetupResponse,
    MFAStatusResponse,
)
from .utils import (
    disable_user_mfa,
    enable_user_mfa,
    is_mfa_enabled_for_user,
    setup_user_mfa,
    verify_user_mfa,
)

__all__ = [
    "ActivityLimitError",
    "DataCollectionError",
    "DataIntegrityError",
    "DatabaseConnectionError",
    "DiskSpaceError",
    "ExportError",
    # Services
    "ExportService",
    "ExportTimeoutError",
    "FileFormatError",
    "FileSizeError",
    "FileSystemError",
    "ImportService",
    "ImportTimeoutError",
    "ImportValidationError",
    "JSONParseError",
    # Schemas
    "MFARequest",
    # MFA Store
    "MFASecretStore",
    "MFASetupRequest",
    "MFASetupResponse",
    "MFAStatusResponse",
    "MemoryAllocationError",
    "ProfileImportError",
    # Exceptions
    "ProfileOperationError",
    "RedisMFASecretStore",
    "SchemaValidationError",
    "ZipCreationError",
    "ZipStructureError",
    "disable_user_mfa",
    "enable_user_mfa",
    "is_mfa_enabled_for_user",
    # Utils
    "setup_user_mfa",
    "verify_user_mfa",
]
