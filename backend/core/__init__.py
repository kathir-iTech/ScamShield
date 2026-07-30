from core.logger import StructuredLogger, logger, reconfigure
from core.metrics import Metrics, metrics
from core.context import (
    get_request_id, get_correlation_id, get_user_id, get_pipeline_id,
    get_request_context, set_request_context, set_user_id, set_pipeline_id,
    clear_request_context,
)
from core.exceptions import (
    ScamShieldError, AuthenticationError, ConfigurationError, ModelLoadError,
    ValidationError, EmptyTextError, TextTooLongError, InvalidImageError,
    ImageExtractionError, OCRProcessingError, ServiceError, MLServiceError,
    RulesServiceError, IntelServiceError, EvidenceServiceError, AssessmentError,
    ReportError, FileAccessError, DatasetNotFoundError, PathTraversalError,
    TextTooLargeError, UnicodeNormalizationError, ImageDecompressionBombError,
    ImageDimensionError, ImageCorruptedError, PipelineStageError, InputSanitisationError,
)
from core.middleware import RequestIDMiddleware
from core.security import (
    SecurityHeadersMiddleware, RateLimitMiddleware, RequestBodySizeMiddleware,
    JSONStructureValidator,
)
from core.abuse import (
    SlidingWindowRateLimiter, RedisSlidingWindowRateLimiter, SlidingWindowRateLimitMiddleware,
    create_rate_limiter, get_rate_limiter, IPRecord,
)
from core.resilience import (
    RequestTimeoutMiddleware, CircuitBreaker, CircuitBreakerState,
    get_circuit_breaker, retry,
)
from core.calibration import (
    calibrate_confidence, confidence_band, recalibrate_thresholds,
    optimize_scoring_weights, recalibrate_final_score,
)
from core.api_keys import APIKeyManager, APIKey, get_api_key_manager
from core.audit import (
    AuditEvent, record_audit_event, record_auth_event, record_auth_failure,
    record_security_event, record_admin_action, record_suspicious_request,
)
from core.diagnostics import get_diagnostics
from core.log_config import LogConfig, load_config
from core.multilingual import (
    detect_language, normalize_tanglish, normalize_hindi_english,
    normalize_unicode, preprocess_multilingual, expand_scam_keywords_for_tamil,
    build_multilingual_indicator_patterns, TAMIL_UNICODE_RANGE, TAMIL_STOP_WORDS,
)
from core.dataset_manager import (
    compute_hash, load_dataset, train_test_split, cross_validation_splits,
    evaluate_dataset_balance, save_manifest, load_manifest, verify_dataset_integrity,
    DATASET_REGISTRY,
)
from core.evaluation_v2 import EvaluationMetrics
from core.auth import (
    AdminAuthRequest, AuthConfig, AuthenticatedUser, LogoutRequest,
    RefreshRequest, TokenPayload, TokenResponse, UserRole,
    configure_auth, create_access_token, create_refresh_token, decode_token,
    get_token_from_header, blacklist_token, is_token_blacklisted,
    mark_refresh_used, is_refresh_reused, reset_blacklist,
    require_auth, require_role, require_admin, optional_auth, get_current_user,
    TokenStore, InMemoryTokenStore, RedisTokenStore,
    create_token_store, get_token_store, set_token_store,
)
from core.constants import *

__all__ = [
    "StructuredLogger", "logger", "reconfigure",
    "Metrics", "metrics",
    "get_request_id", "get_correlation_id", "get_user_id", "get_pipeline_id",
    "get_request_context", "set_request_context", "set_user_id", "set_pipeline_id",
    "clear_request_context",
    "ScamShieldError", "AuthenticationError", "ConfigurationError", "ModelLoadError",
    "ValidationError", "EmptyTextError", "TextTooLongError", "InvalidImageError",
    "ImageExtractionError", "OCRProcessingError", "ServiceError", "MLServiceError",
    "RulesServiceError", "IntelServiceError", "EvidenceServiceError", "AssessmentError",
    "ReportError", "FileAccessError", "DatasetNotFoundError", "PathTraversalError",
    "TextTooLargeError", "UnicodeNormalizationError", "ImageDecompressionBombError",
    "ImageDimensionError", "ImageCorruptedError", "PipelineStageError", "InputSanitisationError",
    "RequestIDMiddleware",
    "SecurityHeadersMiddleware", "RateLimitMiddleware", "RequestBodySizeMiddleware",
    "JSONStructureValidator",
    "SlidingWindowRateLimiter", "RedisSlidingWindowRateLimiter", "SlidingWindowRateLimitMiddleware",
    "create_rate_limiter", "get_rate_limiter", "IPRecord",
    "RequestTimeoutMiddleware", "CircuitBreaker", "CircuitBreakerState",
    "get_circuit_breaker", "retry",
    "calibrate_confidence", "confidence_band", "recalibrate_thresholds",
    "optimize_scoring_weights", "recalibrate_final_score",
    "APIKeyManager", "APIKey", "get_api_key_manager",
    "AuditEvent", "record_audit_event", "record_auth_event", "record_auth_failure",
    "record_security_event", "record_admin_action", "record_suspicious_request",
    "get_diagnostics",
    "LogConfig", "load_config",
    "detect_language", "normalize_tanglish", "normalize_hindi_english",
    "normalize_unicode", "preprocess_multilingual", "expand_scam_keywords_for_tamil",
    "build_multilingual_indicator_patterns", "TAMIL_UNICODE_RANGE", "TAMIL_STOP_WORDS",
    "compute_hash", "load_dataset", "train_test_split", "cross_validation_splits",
    "evaluate_dataset_balance", "save_manifest", "load_manifest", "verify_dataset_integrity",
    "DATASET_REGISTRY",
    "EvaluationMetrics",
    "AdminAuthRequest", "AuthConfig", "AuthenticatedUser", "LogoutRequest",
    "RefreshRequest", "TokenPayload", "TokenResponse", "UserRole",
    "configure_auth", "create_access_token", "create_refresh_token", "decode_token",
    "get_token_from_header", "blacklist_token", "is_token_blacklisted",
    "mark_refresh_used", "is_refresh_reused", "reset_blacklist",
    "require_auth", "require_role", "require_admin", "optional_auth", "get_current_user",
    "TokenStore", "InMemoryTokenStore", "RedisTokenStore",
    "create_token_store", "get_token_store", "set_token_store",
]
