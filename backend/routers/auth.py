import time
from typing import Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from config import settings
from core.abuse import create_rate_limiter, SlidingWindowRateLimiter
from core.auth import (
    AdminAuthRequest, AuthenticatedUser, LogoutRequest,
    RefreshRequest, TokenResponse, UserRole,
    blacklist_token, create_access_token, create_refresh_token,
    decode_token, mark_refresh_used, require_admin, require_auth,
)
from core.audit import record_audit_event, record_auth_event, record_auth_failure
from core.logger import logger

router = APIRouter(tags=["Authentication"])

_auth_limiter = create_rate_limiter(
    name="auth",
    max_requests=settings.AUTH_RATE_LIMIT_MAX,
    window_seconds=settings.AUTH_RATE_LIMIT_WINDOW,
)
_admin_limiter = create_rate_limiter(
    name="auth_admin",
    max_requests=settings.AUTH_ADMIN_RATE_LIMIT_MAX,
    window_seconds=settings.AUTH_ADMIN_RATE_LIMIT_WINDOW,
)


def _check_rate_limit(request: Request, limiter: SlidingWindowRateLimiter) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    if limiter.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication requests. Please try again later.",
        )
    if not limiter.record_request(client_ip, now):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication requests. Please try again later.",
        )


def _add_rate_limit_headers(response: Response, limiter: SlidingWindowRateLimiter, request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    remaining = limiter.remaining(client_ip)
    response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + limiter.window_seconds))


def _get_admin_key(request: Request, body_key: str = "") -> str:
    header_key = request.headers.get("X-Admin-Key", "")
    if header_key:
        return header_key
    return body_key


@router.post("/auth/token", response_model=TokenResponse)
def get_token(request: Request, response: Response, body: AdminAuthRequest = None) -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    _check_rate_limit(request, _auth_limiter)
    _add_rate_limit_headers(response, _auth_limiter, request)

    expected_key = settings.CLIENT_API_KEY
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Client authentication not configured",
        )

    body_key = body.admin_key if body else ""
    client_key = _get_admin_key(request, body_key)
    if not client_key or client_key != expected_key:
        record_auth_failure(detail="Token request with invalid client API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client API key",
        )

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
def get_admin_token(request: Request, response: Response, body: AdminAuthRequest) -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    _check_rate_limit(request, _admin_limiter)
    _add_rate_limit_headers(response, _admin_limiter, request)

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

    admin_key = _get_admin_key(request, body.admin_key)
    if not admin_key or admin_key != expected_key:
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
def refresh_token(request: Request, response: Response, body: RefreshRequest) -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    _check_rate_limit(request, _auth_limiter)
    _add_rate_limit_headers(response, _auth_limiter, request)

    refresh_token_str = body.refresh_token
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
def logout(request: Request, response: Response, body: LogoutRequest) -> Dict:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")

    _check_rate_limit(request, _auth_limiter)
    _add_rate_limit_headers(response, _auth_limiter, request)

    refresh_token_str = body.refresh_token
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
def revoke_token(request: Request, response: Response, token_data: Dict[str, str],
                 user: AuthenticatedUser = Depends(require_auth)) -> Dict:
    _check_rate_limit(request, _auth_limiter)
    _add_rate_limit_headers(response, _auth_limiter, request)

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
def verify_token(request: Request, response: Response, token_data: Dict[str, str]) -> Dict:
    _check_rate_limit(request, _auth_limiter)
    _add_rate_limit_headers(response, _auth_limiter, request)

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
