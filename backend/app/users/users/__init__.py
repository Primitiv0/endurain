"""
User module for user account management and authentication.

This module provides comprehensive user management including
account creation, profile updates, authentication, MFA support,
email verification, and admin approval workflows.

Exports:
    - CRUD: get_all_users, get_users_number,
      get_users_with_pagination, get_user_by_username,
      get_user_by_email, get_user_by_id, get_users_admin,
      create_user, create_signup_user, edit_user, approve_user,
      verify_user_email, edit_user_password, update_user_photo,
      update_user_mfa, delete_user
    - Schemas: UsersBase, Users, UsersRead, UsersMe, UsersSignup,
      UsersCreate, UsersEditPassword, UsersListResponse
    - Models: Users (ORM model)
    - Enums: Gender, Language, WeekDay, UserAccessType
    - Utils: get_user_by_id_or_404, get_admin_users_or_404,
      check_password_and_hash, check_user_is_active,
      create_user_default_data, save_user_image_file,
      delete_user_photo_filesystem
"""

from .crud import (
    approve_user,
    create_signup_user,
    create_user,
    delete_user,
    edit_user,
    edit_user_password,
    get_all_users,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    get_users_admin,
    get_users_number,
    get_users_with_pagination,
    update_user_mfa,
    update_user_photo,
    verify_user_email,
)
from .models import Users as UsersModel
from .schema import (
    Gender,
    Language,
    UserAccessType,
    Users,
    UsersBase,
    UsersCreate,
    UsersEditPassword,
    UsersListResponse,
    UsersMe,
    UsersRead,
    UsersSignup,
    WeekDay,
)
from .utils import (
    check_password_and_hash,
    check_user_is_active,
    create_user_default_data,
    delete_user_photo_filesystem,
    get_admin_users_or_404,
    get_user_by_id_or_404,
    save_user_image_file,
)

__all__ = [
    # Enums
    "Gender",
    "Language",
    "UserAccessType",
    "Users",
    # Pydantic schemas
    "UsersBase",
    "UsersCreate",
    "UsersEditPassword",
    "UsersListResponse",
    "UsersMe",
    # Database model
    "UsersModel",
    "UsersRead",
    "UsersSignup",
    "WeekDay",
    "approve_user",
    "check_password_and_hash",
    "check_user_is_active",
    "create_signup_user",
    "create_user",
    "create_user_default_data",
    "delete_user",
    "delete_user_photo_filesystem",
    "edit_user",
    "edit_user_password",
    "get_admin_users_or_404",
    # CRUD operations
    "get_all_users",
    "get_user_by_email",
    "get_user_by_id",
    # Utility functions
    "get_user_by_id_or_404",
    "get_user_by_username",
    "get_users_admin",
    "get_users_number",
    "get_users_with_pagination",
    "save_user_image_file",
    "update_user_mfa",
    "update_user_photo",
    "verify_user_email",
]
