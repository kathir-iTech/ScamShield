from __future__ import annotations

import os
import time
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from config import settings
from core.abuse import SlidingWindowRateLimiter, create_rate_limiter
from core.audit import record_audit_event
from core.auth import AuthenticatedUser, require_auth
from core.auth.jwt import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    revoke_all_for_user,
)
from core.auth.models import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserRole,
)
from core.auth.users import authenticate, change_password, get_user, register_user
from core.storage.repositories import DuplicateUserError, RateLimitRepo

router = APIRouter(tags=["Accounts"])

_RATE_WINDOW_SECONDS: int = 60
_BLOCK_SECONDS: int = 60
_REGISTER_RATE_LIMIT: int = 10
_LOGIN_IP_RATE_LIMIT: int = 30
_LOGIN_EMAIL_RATE_LIMIT: int = 20

_register_limiter = create_rate_limiter(
    name="register",
    max_requests=_REGISTER_RATE_LIMIT,
    window_seconds=_RATE_WINDOW_SECONDS,
)
_login_ip_limiter = create_rate_limiter(
    name="login_ip",
    max_requests=_LOGIN_IP_RATE_LIMIT,
    window_seconds=_RATE_WINDOW_SECONDS,
)
_login_email_limiter = create_rate_limiter(
    name="login_email",
    max_requests=_LOGIN_EMAIL_RATE_LIMIT,
    window_seconds=_RATE_WINDOW_SECONDS,
)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _limit_headers(state: Dict) -> Dict[str, str]:
    retry_after = max(int(float(state.get("blocked_until", 0)) - time.time()), 1)
    if state.get("allowed"):
        retry_after = _RATE_WINDOW_SECONDS
    return {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(int(state.get("limit", 0))),
        "X-RateLimit-Remaining": str(max(int(state.get("remaining", 0)), 0)),
        "X-RateLimit-Reset": str(int(float(state.get("reset", time.time())))),
    }


def _in_memory_state(limiter: SlidingWindowRateLimiter, key: str) -> Dict:
    now_mono = time.monotonic()
    now = time.time()
    allowed = not limiter.is_blocked(key) and limiter.record_request(key, now_mono)
    return {
        "allowed": allowed,
        "limit": limiter.max_requests,
        "remaining": limiter.remaining(key),
        "reset": now + limiter.window_seconds,
        "blocked_until": 0.0,
    }


def _enforce_rate_limit(
    request: Request,
    response: Response,
    limiter: SlidingWindowRateLimiter,
    bucket: str,
) -> None:
    state: Optional[Dict] = None
    try:
        state = RateLimitRepo().hit(
            bucket,
            _RATE_WINDOW_SECONDS,
            limiter.max_requests,
            _BLOCK_SECONDS,
        )
    except Exception:
        state = None

    if state is None:
        state = _in_memory_state(limiter, _client_ip(request))

    headers = _limit_headers(state)
    response.headers["X-RateLimit-Limit"] = headers["X-RateLimit-Limit"]
    response.headers["X-RateLimit-Remaining"] = headers["X-RateLimit-Remaining"]
    response.headers["X-RateLimit-Reset"] = headers["X-RateLimit-Reset"]

    if not state["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers=headers,
        )


def _user_response(user: Dict) -> UserResponse:
    return UserResponse(
        id=user.get("id", ""),
        email=user.get("email", ""),
        role=user.get("role", UserRole.AUTHENTICATED.value),
        display_name=user.get("display_name", ""),
        created_at=float(user.get("created_at") or 0.0),
        last_login_at=user.get("last_login_at"),
    )


def _as_role(raw: object) -> UserRole:
    values = {role.value: role for role in UserRole}
    if isinstance(raw, str) and raw in values:
        return values[raw]
    return UserRole.AUTHENTICATED


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(request: Request, response: Response, body: RegisterRequest) -> UserResponse:
    if not settings.REGISTER_ENABLED:
        raise HTTPException(status_code=404, detail="Registration is not enabled")

    _enforce_rate_limit(
        request,
        response,
        _register_limiter,
        f"accounts:register:ip:{_client_ip(request)}",
    )

    try:
        user = register_user(body.email, body.password, display_name=body.display_name)
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_audit_event(
        "auth:register",
        level="INFO",
        detail="Account registered via API",
        client_ip=_client_ip(request),
        metadata={"user_id": user["id"]},
    )
    return _user_response(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(request: Request, response: Response, body: LoginRequest) -> TokenResponse:
    if not settings.AUTH_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    client_ip = _client_ip(request)
    _enforce_rate_limit(
        request, response, _login_ip_limiter, f"accounts:login:ip:{client_ip}"
    )
    _enforce_rate_limit(
        request,
        response,
        _login_email_limiter,
        f"accounts:login:email:{(body.email or '').strip().lower()}",
    )

    user = authenticate(body.email, body.password, client_ip=client_ip)
    role = _as_role(user.get("role"))
    access = create_access_token(subject=user["id"], role=role)
    refresh = create_refresh_token(subject=user["id"], role=role.value)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.AUTH_ACCESS_TOKEN_TTL,
    )


@router.get("/auth/me", response_model=UserResponse)
def me(user: AuthenticatedUser = Depends(require_auth)) -> UserResponse:
    profile = get_user(user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return _user_response(profile)


@router.post("/auth/password/change")
def password_change(
    request: Request,
    body: ChangePasswordRequest,
    user: AuthenticatedUser = Depends(require_auth),
) -> Dict:
    profile = get_user(user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        change_password(user.id, body.old_password, body.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_audit_event(
        "auth:password_changed",
        level="INFO",
        detail="Password changed via API",
        client_ip=_client_ip(request),
        metadata={"user_id": user.id},
    )
    return {"detail": "Password updated"}


@router.post("/auth/logout/all")
def logout_all(
    request: Request,
    user: AuthenticatedUser = Depends(require_auth),
) -> Dict:
    revoked = revoke_all_for_user(user.id, kind="refresh")
    if user.token_id:
        blacklist_token(user.token_id)

    record_audit_event(
        "auth:logout_all",
        level="INFO",
        detail=f"Revoked {revoked} refresh token(s)",
        client_ip=_client_ip(request),
        metadata={"user_id": user.id, "revoked": revoked},
    )
    return {"detail": "Logged out of all sessions", "revoked": revoked}
