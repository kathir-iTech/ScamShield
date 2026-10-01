from core.auth.models import (
    AdminAuthRequest, AuthConfig, AuthenticatedUser, ChangePasswordRequest,
    LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest,
    TokenPayload, TokenResponse, UserResponse, UserRole,
)
from core.auth.jwt import (
    blacklist_token, configure as configure_auth,
    create_access_token, create_refresh_token, decode_token,
    encode_access_token, encode_refresh_token, encode_token,
    get_token_from_header, get_blacklist_size, get_used_refresh_count,
    is_token_blacklisted, mark_refresh_used,
    is_refresh_reused, reset_blacklist, revoke_all_for_user,
)
from core.auth.deps import (
    get_current_user,
    optional_auth,
    require_admin,
    require_auth,
    require_auth_if_enabled,
    require_role,
)
from core.auth.passwords import hash_password, password_strength_errors, verify_password
from core.auth.users import authenticate, change_password, get_user, register_user
from core.auth.token_store import (
    TokenStore, InMemoryTokenStore, RedisTokenStore, SqliteTokenStore,
    create_token_store, get_token_store, set_token_store,
)

__all__ = [
    "AdminAuthRequest", "AuthConfig", "AuthenticatedUser", "ChangePasswordRequest",
    "LoginRequest", "LogoutRequest", "RefreshRequest", "RegisterRequest",
    "TokenPayload", "TokenResponse", "UserResponse", "UserRole",
    "configure_auth",
    "create_access_token", "create_refresh_token", "decode_token", "get_token_from_header",
    "encode_access_token", "encode_refresh_token", "encode_token",
    "blacklist_token", "is_token_blacklisted", "mark_refresh_used",
    "is_refresh_reused", "reset_blacklist", "revoke_all_for_user",
    "get_blacklist_size", "get_used_refresh_count",
    "hash_password", "password_strength_errors", "verify_password",
    "authenticate", "change_password", "get_user", "register_user",
    "require_auth", "require_auth_if_enabled", "require_role", "require_admin",
    "optional_auth", "get_current_user",
    "TokenStore", "InMemoryTokenStore", "RedisTokenStore", "SqliteTokenStore",
    "create_token_store", "get_token_store", "set_token_store",
]
