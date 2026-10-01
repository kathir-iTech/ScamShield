from __future__ import annotations

from typing import Any, Dict, Optional

from core.audit import record_auth_event, record_auth_failure
from core.auth.passwords import hash_password, password_strength_errors, verify_password
from core.exceptions import AuthenticationError
from core.storage.repositories import DuplicateUserError, UserRepo

_LOCKOUT_THRESHOLD_DEFAULT: int = 5
_LOCKOUT_SECONDS_DEFAULT: int = 900


def _lockout_settings() -> tuple[int, int]:
    try:
        from config import settings

        threshold = int(getattr(settings, "LOCKOUT_THRESHOLD", _LOCKOUT_THRESHOLD_DEFAULT))
        seconds = int(getattr(settings, "LOCKOUT_SECONDS", _LOCKOUT_SECONDS_DEFAULT))
    except Exception:  # pragma: no cover - settings unavailable in isolated contexts
        threshold, seconds = _LOCKOUT_THRESHOLD_DEFAULT, _LOCKOUT_SECONDS_DEFAULT
    return max(threshold, 1), max(seconds, 0)


def normalise_email(email: str) -> str:
    return (email or "").strip().lower()


def register_user(
    email: str,
    password: str,
    display_name: str = "",
    role: str = "authenticated",
) -> Dict[str, Any]:
    normalised = normalise_email(email)
    if not normalised:
        raise ValueError("Email is required")

    errors = password_strength_errors(password)
    if errors:
        raise ValueError("; ".join(errors))

    repo = UserRepo()
    if repo.get_by_email(normalised) is not None:
        raise DuplicateUserError(f"An account with this email already exists: {normalised}")

    user = repo.create(
        normalised,
        hash_password(password),
        role=role,
        display_name=(display_name or "").strip(),
    )
    record_auth_event(
        "auth:register",
        detail=f"Account registered for {normalised}",
        user_id=user["id"],
    )
    return user


def authenticate(email: str, password: str, client_ip: str = "") -> Dict[str, Any]:
    normalised = normalise_email(email)
    repo = UserRepo()
    user = repo.get_by_email(normalised)
    threshold, lock_seconds = _lockout_settings()

    if user is None:
        verify_password(password or "", "")
        record_auth_failure(
            detail="Login failed for unknown account", client_ip=client_ip
        )
        raise AuthenticationError("Invalid email or password")

    if UserRepo.is_locked(user):
        record_auth_failure(
            detail=f"Login blocked, account locked for {normalised}", client_ip=client_ip
        )
        raise AuthenticationError(
            "Account temporarily locked after too many failed attempts"
        )

    if user.get("status") != "active":
        record_auth_failure(
            detail=f"Login blocked, account status {user.get('status')}", client_ip=client_ip
        )
        raise AuthenticationError("Account is not active")

    if not verify_password(password or "", user["password_hash"]):
        locked = repo.record_login_failure(user["id"], threshold, lock_seconds)
        record_auth_failure(
            detail="Login failed with invalid password", client_ip=client_ip
        )
        if locked:
            raise AuthenticationError(
                "Account temporarily locked after too many failed attempts"
            )
        raise AuthenticationError("Invalid email or password")

    repo.record_login_success(user["id"])
    record_auth_event(
        "auth:login",
        detail=f"Login succeeded for {normalised}",
        user_id=user["id"],
    )
    refreshed = repo.get_by_id(user["id"])
    return refreshed or user


def change_password(
    user_id: str, old_password: str, new_password: str
) -> Dict[str, Any]:
    repo = UserRepo()
    user = repo.get_by_id(user_id)
    if user is None:
        raise AuthenticationError("Account not found")

    if not verify_password(old_password or "", user["password_hash"]):
        record_auth_failure(
            detail="Password change rejected, current password mismatch"
        )
        raise AuthenticationError("Current password is incorrect")

    errors = password_strength_errors(new_password)
    if errors:
        raise ValueError("; ".join(errors))

    repo.update_password(user_id, hash_password(new_password))
    record_auth_event(
        "auth:password_changed",
        detail="Password changed successfully",
        user_id=user_id,
    )
    updated = repo.get_by_id(user_id)
    return updated or user


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    return UserRepo().get_by_id(user_id)


__all__ = [
    "AuthenticationError",
    "DuplicateUserError",
    "authenticate",
    "change_password",
    "get_user",
    "normalise_email",
    "register_user",
]
