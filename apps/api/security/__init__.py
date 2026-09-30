"""Security package exports."""

from security.auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
    hash_aadhaar,
    hash_refresh_token,
)
decode_token = decode_access_token
from security.rbac import (
    get_current_user,
    get_current_active_user,
    require_roles,
    require_permissions,
)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "verify_password",
    "hash_aadhaar",
    "hash_refresh_token",
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "require_permissions",
]
