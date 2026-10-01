import json
import os
import re
import time
import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from config import settings
from core.abuse import SlidingWindowRateLimiter, create_rate_limiter
from core.audit import record_audit_event
from core.context import get_request_id
from core.logger import logger
from core.storage.db import get_db

try:
    from core.storage.repositories import FeedbackRepo
except ImportError:
    FeedbackRepo = None

router = APIRouter(tags=["Feedback"])

_VERDICTS = ("correct", "incorrect", "unsure")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


_feedback_limiter = create_rate_limiter(
    name="feedback",
    max_requests=_env_int("SCAMSHIELD_FEEDBACK_RATE_LIMIT_MAX", 30),
    window_seconds=_env_int("SCAMSHIELD_FEEDBACK_RATE_LIMIT_WINDOW", 60),
)

_REDACTED_PATTERNS = (
    (re.compile(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b"), "<CARD>"),
    (re.compile(r"\b\d{10,}\b"), "<REDACTED>"),
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "<EMAIL>"),
    (re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3}[-.\s]?\d{4}"), "<PHONE>"),
    (re.compile(r"\bupi\b", re.IGNORECASE), "<UPI>"),
    (re.compile(r"\botp\b", re.IGNORECASE), "<OTP>"),
    (re.compile(r"\b(?:pan|aadhar|voter|driving\s*license)\b", re.IGNORECASE), "<ID>"),
)


def _mask_pii(text: str) -> str:
    if not text:
        return text
    masked = text
    for pattern, replacement in _REDACTED_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


class FeedbackRequest(BaseModel):
    model_config = {"extra": "forbid"}

    analysis_id: str = Field(default="", max_length=64, description="Analysis this feedback refers to")
    verdict: str = Field(..., description="Was the verdict correct, incorrect, or unsure")
    corrected_label: str = Field(default="", max_length=120, description="Label the reviewer believes is right")
    note: str = Field(default="", max_length=4000, description="Free text explanation")

    @field_validator("verdict")
    @classmethod
    def _validate_verdict(cls, value: str) -> str:
        normalised = (value or "").strip().lower()
        if normalised not in _VERDICTS:
            raise ValueError(f"verdict must be one of: {', '.join(_VERDICTS)}")
        return normalised

    @field_validator("analysis_id", "corrected_label", "note")
    @classmethod
    def _strip_fields(cls, value: str) -> str:
        return (value or "").strip()


class FeedbackResponse(BaseModel):
    detail: str
    id: str


def _check_rate_limit(request: Request, limiter: SlidingWindowRateLimiter) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    if limiter.is_blocked(client_ip):
        retry_after = max(int(limiter.get_block_time(client_ip)), 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many feedback submissions. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    if not limiter.record_request(client_ip, now):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many feedback submissions. Please try again later.",
            headers={"Retry-After": str(limiter.window_seconds)},
        )


def _add_rate_limit_headers(response: Response, limiter: SlidingWindowRateLimiter, request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(limiter.remaining(client_ip))
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + limiter.window_seconds))


def _store_feedback(
    feedback_id: str,
    analysis_id: str,
    user_id: str,
    verdict: str,
    corrected_label: str,
    note: str,
    context: Dict[str, str],
    created_at: float,
) -> str:
    if FeedbackRepo is not None:
        for method_name in ("create", "insert", "add", "save"):
            method = getattr(FeedbackRepo, method_name, None)
            if not callable(method):
                continue
            try:
                created = method(
                    id=feedback_id,
                    analysis_id=analysis_id,
                    user_id=user_id,
                    verdict=verdict,
                    corrected_label=corrected_label,
                    note=note,
                    context=json.dumps(context),
                    resolved=0,
                    created_at=created_at,
                )
                if isinstance(created, str) and created:
                    return created
                return feedback_id
            except Exception as exc:
                logger.warning(
                    "FeedbackRepo.%s failed, falling back to direct SQL: %s",
                    method_name,
                    exc,
                )
                break

    db = get_db()
    db.execute(
        "INSERT INTO feedback "
        "(id, analysis_id, user_id, verdict, corrected_label, note, context, resolved, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            feedback_id,
            analysis_id,
            user_id,
            verdict,
            corrected_label,
            note,
            json.dumps(context),
            0,
            created_at,
        ),
    )
    return feedback_id


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_feedback(request: Request, response: Response, payload: FeedbackRequest) -> FeedbackResponse:
    _check_rate_limit(request, _feedback_limiter)
    _add_rate_limit_headers(response, _feedback_limiter, request)

    client_ip = request.client.host if request.client else "unknown"
    user_id = ""
    if settings.AUTH_ENABLED:
        user_id = getattr(request.state, "user_id", "") or ""

    note = _mask_pii(payload.note)
    feedback_id = uuid.uuid4().hex
    created_at = time.time()
    context = {"request_id": get_request_id(), "source": "api"}

    try:
        _store_feedback(
            feedback_id=feedback_id,
            analysis_id=payload.analysis_id,
            user_id=user_id,
            verdict=payload.verdict,
            corrected_label=payload.corrected_label,
            note=note,
            context=context,
            created_at=created_at,
        )
    except Exception as exc:
        logger.error("Failed to store feedback: %s", exc)
        record_audit_event(
            "feedback:rejected",
            level="ERROR",
            detail="Feedback could not be stored",
            resource="feedback",
            client_ip=client_ip,
            metadata={"verdict": payload.verdict, "analysis_id": payload.analysis_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feedback could not be stored. Please try again later.",
        ) from exc

    record_audit_event(
        "feedback:submitted",
        level="INFO",
        detail=f"Feedback recorded with verdict '{payload.verdict}'",
        resource="feedback",
        client_ip=client_ip,
        metadata={
            "feedback_id": feedback_id,
            "analysis_id": payload.analysis_id,
            "verdict": payload.verdict,
            "corrected_label": payload.corrected_label,
            "has_note": bool(note),
        },
    )

    return FeedbackResponse(detail="Feedback accepted", id=feedback_id)
