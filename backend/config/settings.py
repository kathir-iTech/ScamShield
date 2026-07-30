import os
from typing import List

from core.config.assessment import *
from core.config.auth import *
from core.config.connectors import *
from core.config.evaluation import *
from core.config.investigation import *
from core.config.knowledge import *
from core.config.profiles import get_profile
from core.config.reasoning import *
from core.config.refinement import *
from core.config.reporting import *
from core.config.security import *
from core.config.validation import *

# -- Paths (remain here — not configurable via env) --
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_FOLDER: str = os.path.join(BASE_DIR, "models")
DATA_FOLDER: str = os.path.join(BASE_DIR, "data")

MODEL_PATH: str = os.path.join(MODEL_FOLDER, "model.joblib")
VECTORIZER_PATH: str = os.path.join(MODEL_FOLDER, "vectorizer.joblib")
DATASET_PATH: str = os.path.join(DATA_FOLDER, "scam_dataset.csv")
V2_DATASET_PATH: str = os.path.join(DATA_FOLDER, "dataset_v2_beta.csv")
V2_MODEL_PATH: str = os.path.join(MODEL_FOLDER, "v2_model.joblib")
V2_VECTORIZER_PATH: str = os.path.join(MODEL_FOLDER, "v2_vectorizer.joblib")

# -- Env-var overrides (applied at module load time) --
_dataset_path = os.getenv("SCAMSHIELD_DATASET_PATH", "")
if _dataset_path:
    DATASET_PATH = _dataset_path
MAX_TEXT_LENGTH = int(os.getenv("SCAMSHIELD_MAX_TEXT_LENGTH", str(MAX_TEXT_LENGTH)))
MAX_FILE_SIZE_MB = int(os.getenv("SCAMSHIELD_MAX_FILE_SIZE_MB", str(MAX_FILE_SIZE_MB)))
CONNECTOR_TIMEOUT = int(os.getenv("SCAMSHIELD_CONNECTOR_TIMEOUT", str(CONNECTOR_TIMEOUT)))
CONNECTOR_RETRY_COUNT = int(os.getenv("SCAMSHIELD_CONNECTOR_RETRY_COUNT", str(CONNECTOR_RETRY_COUNT)))
CONNECTOR_PARALLELISM = int(os.getenv("SCAMSHIELD_CONNECTOR_PARALLELISM", str(CONNECTOR_PARALLELISM)))
CONNECTOR_CACHE_TTL = int(os.getenv("SCAMSHIELD_CONNECTOR_CACHE_TTL", str(CONNECTOR_CACHE_TTL)))
CONNECTOR_MAX_RESULTS = int(os.getenv("SCAMSHIELD_CONNECTOR_MAX_RESULTS", str(CONNECTOR_MAX_RESULTS)))
SAFE_BROWSING_TIMEOUT = int(os.getenv("SCAMSHIELD_SAFE_BROWSING_TIMEOUT", str(SAFE_BROWSING_TIMEOUT)))
SAFE_BROWSING_CACHE_TTL = int(os.getenv("SCAMSHIELD_SAFE_BROWSING_CACHE_TTL", str(SAFE_BROWSING_CACHE_TTL)))
SAFE_BROWSING_MAX_BATCH = int(os.getenv("SCAMSHIELD_SAFE_BROWSING_MAX_BATCH", str(SAFE_BROWSING_MAX_BATCH)))

_sb_key = os.getenv("SCAMSHIELD_SAFE_BROWSING_API_KEY", "")
if _sb_key:
    SAFE_BROWSING_API_KEY = _sb_key

_sb_enabled = os.getenv("SCAMSHIELD_SAFE_BROWSING_ENABLED", "")
if _sb_enabled:
    SAFE_BROWSING_ENABLED = _sb_enabled.lower() in ("1", "true", "yes")

# -- Auth overrides --
_auth_enabled = os.getenv("SCAMSHIELD_AUTH_ENABLED", "")
if _auth_enabled:
    AUTH_ENABLED = _auth_enabled.lower() in ("1", "true", "yes")

_jwt_secret = os.getenv("SCAMSHIELD_JWT_SECRET", "")
if _jwt_secret:
    AUTH_JWT_SECRET = _jwt_secret

_jwt_access_ttl = os.getenv("SCAMSHIELD_JWT_ACCESS_TTL", "")
if _jwt_access_ttl:
    try:
        AUTH_ACCESS_TOKEN_TTL = int(_jwt_access_ttl)
    except ValueError:
        pass

_jwt_refresh_ttl = os.getenv("SCAMSHIELD_JWT_REFRESH_TTL", "")
if _jwt_refresh_ttl:
    try:
        AUTH_REFRESH_TOKEN_TTL = int(_jwt_refresh_ttl)
    except ValueError:
        pass

_admin_api_key = os.getenv("SCAMSHIELD_ADMIN_API_KEY", "")
if _admin_api_key:
    ADMIN_API_KEY = _admin_api_key

_client_api_key = os.getenv("SCAMSHIELD_CLIENT_API_KEY", "")
if _client_api_key:
    CLIENT_API_KEY = _client_api_key

_jwt_clock_skew = os.getenv("SCAMSHIELD_JWT_CLOCK_SKEW", "")
if _jwt_clock_skew:
    try:
        JWT_CLOCK_SKEW_SECONDS = int(_jwt_clock_skew)
    except ValueError:
        pass

# -- Redis / Token store --
_redis_url = os.getenv("SCAMSHIELD_REDIS_URL", "")
if _redis_url:
    REDIS_URL = _redis_url

# -- Auth rate limit overrides --
_auth_rl_max = os.getenv("SCAMSHIELD_AUTH_RATE_LIMIT_MAX", "")
if _auth_rl_max:
    try:
        AUTH_RATE_LIMIT_MAX = int(_auth_rl_max)
    except ValueError:
        pass

_auth_rl_window = os.getenv("SCAMSHIELD_AUTH_RATE_LIMIT_WINDOW", "")
if _auth_rl_window:
    try:
        AUTH_RATE_LIMIT_WINDOW = int(_auth_rl_window)
    except ValueError:
        pass

_auth_admin_rl_max = os.getenv("SCAMSHIELD_AUTH_ADMIN_RATE_LIMIT_MAX", "")
if _auth_admin_rl_max:
    try:
        AUTH_ADMIN_RATE_LIMIT_MAX = int(_auth_admin_rl_max)
    except ValueError:
        pass

_auth_admin_rl_window = os.getenv("SCAMSHIELD_AUTH_ADMIN_RATE_LIMIT_WINDOW", "")
if _auth_admin_rl_window:
    try:
        AUTH_ADMIN_RATE_LIMIT_WINDOW = int(_auth_admin_rl_window)
    except ValueError:
        pass

# -- OCR overrides --
_ocr_workers = os.getenv("SCAMSHIELD_OCR_MAX_WORKERS", "")
if _ocr_workers:
    try:
        OCR_MAX_WORKERS = int(_ocr_workers)
    except ValueError:
        pass

_ocr_dim = os.getenv("SCAMSHIELD_OCR_MAX_IMAGE_DIMENSION", "")
if _ocr_dim:
    try:
        OCR_MAX_IMAGE_DIMENSION = int(_ocr_dim)
    except ValueError:
        pass

_ocr_pixels = os.getenv("SCAMSHIELD_OCR_MAX_IMAGE_PIXELS", "")
if _ocr_pixels:
    try:
        OCR_MAX_IMAGE_PIXELS = int(_ocr_pixels)
    except ValueError:
        pass

# -- CORS / Security overrides --
_cors_origins = os.getenv("SCAMSHIELD_CORS_ORIGINS", "")
if _cors_origins:
    CORS_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]

_rate_limit_max = os.getenv("SCAMSHIELD_RATE_LIMIT_MAX", "")
if _rate_limit_max:
    try:
        RATE_LIMIT_MAX_REQUESTS = int(_rate_limit_max)
    except ValueError:
        pass

_rate_limit_window = os.getenv("SCAMSHIELD_RATE_LIMIT_WINDOW", "")
if _rate_limit_window:
    try:
        RATE_LIMIT_WINDOW_SECONDS = int(_rate_limit_window)
    except ValueError:
        pass

_env = os.getenv("SCAMSHIELD_ENVIRONMENT", "")
if _env:
    ENVIRONMENT = _env
    profile = get_profile(ENVIRONMENT)
    if not CORS_ORIGINS or CORS_ORIGINS == ["*"]:
        CORS_ORIGINS = list(profile.cors_origins) if profile.cors_origins else []
    if RATE_LIMIT_MAX_REQUESTS == 100:
        RATE_LIMIT_MAX_REQUESTS = profile.rate_limit_max
    if RATE_LIMIT_WINDOW_SECONDS == 60:
        RATE_LIMIT_WINDOW_SECONDS = profile.rate_limit_window
    if MAX_REQUEST_BODY_SIZE == 10 * 1024 * 1024:
        MAX_REQUEST_BODY_SIZE = profile.max_request_body_mb * 1024 * 1024
    DEBUG = profile.debug

_body_size = os.getenv("SCAMSHIELD_MAX_REQUEST_BODY_MB", "")
if _body_size:
    try:
        MAX_REQUEST_BODY_SIZE = int(_body_size) * 1024 * 1024
    except ValueError:
        pass


def validate_config() -> List[str]:
    errors: List[str] = []

    raw_text_length = os.getenv("SCAMSHIELD_MAX_TEXT_LENGTH", str(MAX_TEXT_LENGTH))
    try:
        val = int(raw_text_length)
        if val <= 0:
            errors.append(f"SCAMSHIELD_MAX_TEXT_LENGTH must be positive, got {val}")
        if val > 100000:
            errors.append(f"SCAMSHIELD_MAX_TEXT_LENGTH too large ({val}), max 100000")
    except (ValueError, TypeError):
        errors.append(f"SCAMSHIELD_MAX_TEXT_LENGTH invalid: '{raw_text_length}'")

    raw_file_size = os.getenv("SCAMSHIELD_MAX_FILE_SIZE_MB", str(MAX_FILE_SIZE_MB))
    try:
        val = int(raw_file_size)
        if val <= 0:
            errors.append(f"SCAMSHIELD_MAX_FILE_SIZE_MB must be positive, got {val}")
        if val > 100:
            errors.append(f"SCAMSHIELD_MAX_FILE_SIZE_MB too large ({val}), max 100")
    except (ValueError, TypeError):
        errors.append(f"SCAMSHIELD_MAX_FILE_SIZE_MB invalid: '{raw_file_size}'")

    if not SUPPORTED_IMAGE_TYPES:
        errors.append("SUPPORTED_IMAGE_TYPES is empty — no image types allowed")

    MODEL_FOLDER_PATH = MODEL_FOLDER
    if not os.path.isdir(MODEL_FOLDER_PATH):
        errors.append(f"Model directory not found: {MODEL_FOLDER_PATH}")

    DATA_FOLDER_PATH = DATA_FOLDER
    if not os.path.isdir(DATA_FOLDER_PATH):
        errors.append(f"Data directory not found: {DATA_FOLDER_PATH}")

    log_level = os.getenv("SCAMSHIELD_LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        errors.append(
            f"SCAMSHIELD_LOG_LEVEL invalid: '{log_level}'. "
            f"Valid: {', '.join(sorted(valid_levels))}"
        )

    log_format = os.getenv("SCAMSHIELD_LOG_FORMAT", "text").lower()
    if log_format not in ("json", "text"):
        errors.append(f"SCAMSHIELD_LOG_FORMAT invalid: '{log_format}'. Valid: json, text")

    log_output = os.getenv("SCAMSHIELD_LOG_OUTPUT", "stdout").lower()
    if log_output not in ("stdout", "file", "both"):
        errors.append(f"SCAMSHIELD_LOG_OUTPUT invalid: '{log_output}'. Valid: stdout, file, both")

    log_file = os.getenv("SCAMSHIELD_LOG_FILE", "")
    if log_output in ("file", "both") and not log_file:
        errors.append("SCAMSHIELD_LOG_FILE required when SCAMSHIELD_LOG_OUTPUT is 'file' or 'both'")

    # -- Auth validation --
    if AUTH_ENABLED and not AUTH_JWT_SECRET:
        errors.append("SCAMSHIELD_JWT_SECRET required when SCAMSHIELD_AUTH_ENABLED is true")

    if AUTH_ENABLED and not ADMIN_API_KEY:
        errors.append("SCAMSHIELD_ADMIN_API_KEY required when SCAMSHIELD_AUTH_ENABLED is true")

    if AUTH_ENABLED and not CLIENT_API_KEY:
        errors.append("SCAMSHIELD_CLIENT_API_KEY required when SCAMSHIELD_AUTH_ENABLED is true")

    jwt_clock_skew = int(os.getenv("SCAMSHIELD_JWT_CLOCK_SKEW", str(JWT_CLOCK_SKEW_SECONDS)))
    if jwt_clock_skew < 0:
        errors.append(f"SCAMSHIELD_JWT_CLOCK_SKEW must be non-negative, got {jwt_clock_skew}")
    if jwt_clock_skew > 300:
        errors.append(f"SCAMSHIELD_JWT_CLOCK_SKEW too high ({jwt_clock_skew}s), maximum 300s")

    jwt_access_ttl = int(os.getenv("SCAMSHIELD_JWT_ACCESS_TTL", str(AUTH_ACCESS_TOKEN_TTL)))
    if jwt_access_ttl < 60:
        errors.append(f"SCAMSHIELD_JWT_ACCESS_TTL too low ({jwt_access_ttl}s), minimum 60s")
    if jwt_access_ttl > 86400:
        errors.append(f"SCAMSHIELD_JWT_ACCESS_TTL too high ({jwt_access_ttl}s), maximum 86400s (24h)")

    jwt_refresh_ttl = int(os.getenv("SCAMSHIELD_JWT_REFRESH_TTL", str(AUTH_REFRESH_TOKEN_TTL)))
    if jwt_refresh_ttl < 3600:
        errors.append(f"SCAMSHIELD_JWT_REFRESH_TTL too low ({jwt_refresh_ttl}s), minimum 3600s")
    if jwt_refresh_ttl > 86400 * 90:
        errors.append(f"SCAMSHIELD_JWT_REFRESH_TTL too high ({jwt_refresh_ttl}s), maximum 90 days")

    # -- CORS validation --
    if ENVIRONMENT == "production":
        cors_origins_raw = os.getenv("SCAMSHIELD_CORS_ORIGINS", "")
        if not cors_origins_raw:
            errors.append("SCAMSHIELD_CORS_ORIGINS required in production")
        if cors_origins_raw == "*":
            errors.append("Wildcard CORS_ORIGINS not allowed in production")

    # -- Environment validation --
    valid_envs = {"development", "testing", "staging", "production", "local"}
    if ENVIRONMENT not in valid_envs:
        errors.append(f"SCAMSHIELD_ENVIRONMENT invalid: '{ENVIRONMENT}'. Valid: {', '.join(sorted(valid_envs))}")

    if ENVIRONMENT == "production":
        if not AUTH_ENABLED:
            errors.append("AUTH_ENABLED must be true in production")
        if DEBUG:
            errors.append("DEBUG must be false in production")
        if not MAX_REQUEST_BODY_SIZE:
            errors.append("MAX_REQUEST_BODY_SIZE must be set in production")

    # -- Container filesystem validation (production) --
    if ENVIRONMENT == "production":
        model_dir = os.path.dirname(MODEL_PATH)
        if model_dir and not os.access(model_dir, os.R_OK):
            errors.append(f"Model directory not readable: {model_dir}")
        log_path = os.getenv("SCAMSHIELD_LOG_FILE", "")
        if log_path:
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.access(log_dir, os.W_OK):
                errors.append(f"Log directory not writable: {log_dir}")

    return errors
