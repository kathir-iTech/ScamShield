import time
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from core.auth import (
    AdminAuthRequest, AuthenticatedUser, LogoutRequest,
    RefreshRequest, TokenResponse, UserRole,
    blacklist_token, create_access_token, create_refresh_token,
    decode_token, mark_refresh_used, require_admin,
)
from core.audit import record_audit_event, record_auth_event, record_auth_failure
from core.logger import logger

router = APIRouter(tags=["Authentication"])


@router.post("/auth/token", response_model=TokenResponse)
def get_token() -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    subject = f"user_{int(time.time())}"
    access = create_access_token(subject=subject, role=UserRole.AUTHENTICATED)
    refresh = create_refresh_token(subject=subject)

    record_auth_event("auth:login", detail="Access token issued", user_id=subject)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.AUTH_ACCESS_TOKEN_TTL,
    )


@router.post("/auth/token/admin", response_model=TokenResponse)
def get_admin_token(request: AdminAuthRequest) -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    expected_key = settings.ADMIN_API_KEY
    if not expected_key:
        record_audit_event(
            "auth:admin_token_failed",
            level="ERROR",
            detail="Admin API key not configured",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication not configured",
        )

    if not request.admin_key or request.admin_key != expected_key:
        record_auth_failure(detail="Admin token request with invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
        )

    subject = f"admin_{int(time.time())}"
    access = create_access_token(subject=subject, role=UserRole.ADMIN)
    refresh = create_refresh_token(subject=subject)

    record_audit_event(
        "auth:admin_token_issued",
        level="INFO",
        detail=f"Admin token issued for {subject}",
    )

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.AUTH_ACCESS_TOKEN_TTL,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest) -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    refresh_token_str = request.refresh_token
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    try:
        payload = decode_token(refresh_token_str)
    except ValueError as exc:
        record_auth_failure(detail=f"Token refresh failed: {exc}")
        raise HTTPException(status_code=401, detail=str(exc))

    if payload.token_type != "refresh":
        record_auth_failure(detail="Invalid token type in refresh")
        raise HTTPException(status_code=401, detail="Invalid token type")

    if not mark_refresh_used(payload.jti):
        record_auth_failure(detail="Refresh token reuse detected")
        blacklist_token(payload.jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has already been used",
        )

    blacklist_token(payload.jti)

    role = UserRole.AUTHENTICATED
    access = create_access_token(subject=payload.sub, role=role)
    refresh = create_refresh_token(subject=payload.sub)

    record_auth_event("auth:token_refresh", detail=f"Token refreshed for {payload.sub}", user_id=payload.sub)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.AUTH_ACCESS_TOKEN_TTL,
    )


@router.post("/auth/logout")
def logout(request: LogoutRequest) -> Dict:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    refresh_token_str = request.refresh_token
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    try:
        payload = decode_token(refresh_token_str)
        if payload.token_type == "access":
            blacklist_token(payload.jti)
        elif payload.token_type == "refresh":
            blacklist_token(payload.jti)
        record_auth_event("auth:logout", detail=f"Token revoked for {payload.sub}", user_id=payload.sub)
    except ValueError:
        pass

    return {"detail": "Logged out successfully"}


@router.post("/auth/revoke")
def revoke_token(token_data: Dict[str, str]) -> Dict:
    token = token_data.get("token", "")
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    try:
        payload = decode_token(token)
        blacklist_token(payload.jti)
        record_audit_event("auth:token_revoked", detail=f"Token revoked for {payload.sub}")
        return {"detail": "Token revoked"}
    except ValueError as exc:
        return {"detail": str(exc)}


@router.post("/auth/verify")
def verify_token(token_data: Dict[str, str]) -> Dict:
    token = token_data.get("token", "")
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    try:
        payload = decode_token(token)
        record_audit_event("auth:token_verify", detail=f"Token verified for {payload.sub}")
        return {"valid": True, "sub": payload.sub, "role": payload.role, "token_type": payload.token_type}
    except ValueError as exc:
        record_auth_failure(detail=f"Token verification failed")
        return {"valid": False, "detail": str(exc)}
