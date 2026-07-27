from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Profile:
    name: str
    debug: bool
    log_level: str
    log_format: str
    cors_origins: List[str]
    rate_limit_max: int
    rate_limit_window: int
    max_request_body_mb: int
    auth_enabled: bool
    jwt_access_ttl: int
    jwt_refresh_ttl: int
    log_output: str = "stdout"
    validate_secrets: bool = False
    fail_fast: bool = False


DEVELOPMENT = Profile(
    name="development",
    debug=True,
    log_level="DEBUG",
    log_format="text",
    cors_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost"],
    rate_limit_max=200,
    rate_limit_window=60,
    max_request_body_mb=10,
    auth_enabled=False,
    jwt_access_ttl=3600,
    jwt_refresh_ttl=86400 * 30,
)

TESTING = Profile(
    name="testing",
    debug=False,
    log_level="INFO",
    log_format="text",
    cors_origins=["*"],
    rate_limit_max=200,
    rate_limit_window=60,
    max_request_body_mb=10,
    auth_enabled=False,
    jwt_access_ttl=3600,
    jwt_refresh_ttl=86400 * 30,
)

STAGING = Profile(
    name="staging",
    debug=False,
    log_level="INFO",
    log_format="json",
    cors_origins=[],
    rate_limit_max=100,
    rate_limit_window=60,
    max_request_body_mb=10,
    auth_enabled=True,
    jwt_access_ttl=1800,
    jwt_refresh_ttl=86400 * 7,
    log_output="both",
    validate_secrets=True,
    fail_fast=True,
)

PRODUCTION = Profile(
    name="production",
    debug=False,
    log_level="INFO",
    log_format="json",
    cors_origins=[],
    rate_limit_max=60,
    rate_limit_window=60,
    max_request_body_mb=5,
    auth_enabled=True,
    jwt_access_ttl=900,
    jwt_refresh_ttl=86400 * 1,
    log_output="both",
    validate_secrets=True,
    fail_fast=True,
)

LOCAL = Profile(
    name="local",
    debug=True,
    log_level="DEBUG",
    log_format="text",
    cors_origins=["*"],
    rate_limit_max=500,
    rate_limit_window=60,
    max_request_body_mb=50,
    auth_enabled=False,
    jwt_access_ttl=86400,
    jwt_refresh_ttl=86400 * 30,
)


PROFILES: dict[str, Profile] = {
    "development": DEVELOPMENT,
    "testing": TESTING,
    "staging": STAGING,
    "production": PRODUCTION,
    "local": LOCAL,
}


def get_profile(name: Optional[str] = None) -> Profile:
    if name is None:
        name = "development"
    return PROFILES.get(name, DEVELOPMENT)
