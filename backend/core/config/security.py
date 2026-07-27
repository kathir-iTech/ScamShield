__all__ = [
    "CORS_ORIGINS", "RATE_LIMIT_MAX_REQUESTS", "RATE_LIMIT_WINDOW_SECONDS",
    "MAX_REQUEST_BODY_SIZE", "ENVIRONMENT", "PROFILE",
]

from typing import List

from core.config.profiles import get_profile

ENVIRONMENT: str = "development"
PROFILE = get_profile(ENVIRONMENT)

CORS_ORIGINS: List[str] = list(PROFILE.cors_origins)
RATE_LIMIT_MAX_REQUESTS: int = PROFILE.rate_limit_max
RATE_LIMIT_WINDOW_SECONDS: int = PROFILE.rate_limit_window
MAX_REQUEST_BODY_SIZE: int = PROFILE.max_request_body_mb * 1024 * 1024
DEBUG: bool = PROFILE.debug
