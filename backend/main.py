import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from core.abuse import SlidingWindowRateLimitMiddleware
from core.auth import configure_auth
from core.constants import SERVICE_NAME, API_VERSION
from core.context import get_correlation_id, get_request_id, set_user_id
from core.exceptions import AuthenticationError, ConfigurationError, ScamShieldError, ValidationError
from core.logger import logger, reconfigure
from core.log_config import load_config
from core.metrics import metrics
from core.middleware import RequestIDMiddleware
from core.resilience import RequestTimeoutMiddleware
from core.security import JSONStructureValidator, RequestBodySizeMiddleware, SecurityHeadersMiddleware
from routers.health import router as health_router
from routers.analyze import router as analyze_router
from routers.auth import router as auth_router
from config import settings
from config.settings import validate_config, REDIS_URL
from core.prometheus_metrics import init_prometheus_metrics, record_prometheus_request, get_prometheus_metrics_endpoint


def _validate_startup() -> None:
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            logger.critical("Configuration error: %s", err)
        raise ConfigurationError(
            f"Startup validation failed with {len(config_errors)} error(s): "
            + "; ".join(config_errors)
        )


def _mask_pii(msg: str) -> str:
    msg = re.sub(r"\b\d{10,}\b", "<REDACTED>", msg)
    msg = re.sub(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b", "<CARD>", msg)
    msg = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", msg)
    msg = re.sub(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "<PHONE>", msg)
    msg = re.sub(r"\bupi\b", "<UPI>", msg, flags=re.IGNORECASE)
    msg = re.sub(r"\botp\b", "<OTP>", msg, flags=re.IGNORECASE)
    msg = re.sub(r"\b(?:pan|aadhar|voter|driving\s*license)\b", "<ID>", msg, flags=re.IGNORECASE)
    return msg


def _verify_startup_prerequisites() -> list:
    errors = []
    required_files = [
        ("Settings", __file__),
        ("Model", settings.MODEL_PATH),
        ("Vectorizer", settings.VECTORIZER_PATH),
    ]
    for label, path in required_files:
        if not os.path.exists(path):
            errors.append(f"{label} file not found: {path}")

    config_errors = []
    if settings.MAX_TEXT_LENGTH <= 0:
        config_errors.append("MAX_TEXT_LENGTH must be positive")
    if settings.MAX_FILE_SIZE_MB <= 0:
        config_errors.append("MAX_FILE_SIZE_MB must be positive")
    if not settings.SUPPORTED_IMAGE_TYPES:
        config_errors.append("No supported image types configured")

    for err in config_errors:
        errors.append(f"Configuration error: {err}")

    writable_dirs = [
        os.path.dirname(settings.MODEL_PATH),
        os.path.dirname(settings.DATASET_PATH) if os.path.exists(os.path.dirname(settings.DATASET_PATH)) else "",
    ]
    for d in writable_dirs:
        if d and not os.access(d, os.W_OK):
            errors.append(f"Directory not writable: {d}")

    return errors


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_cfg = load_config()
    reconfigure(log_cfg)

    if settings.AUTH_ENABLED and settings.AUTH_JWT_SECRET:
        configure_auth(
            secret_key=settings.AUTH_JWT_SECRET,
            access_ttl=settings.AUTH_ACCESS_TOKEN_TTL,
            refresh_ttl=settings.AUTH_REFRESH_TOKEN_TTL,
            clock_skew=settings.JWT_CLOCK_SKEW_SECONDS,
            blacklist_capacity=settings.TOKEN_BLACKLIST_CAPACITY,
            redis_url=REDIS_URL,
        )

    init_prometheus_metrics()
    logger.info("Prometheus metrics initialized")

    logger.info(
        "Wary API starting up — version %s",
        API_VERSION,
        extra={"structured": {"event": "startup", "version": API_VERSION}},
    )

    try:
        _validate_startup()
        logger.info("Configuration validation passed")
    except ConfigurationError:
        logger.critical("Startup aborted due to configuration errors")
        raise

    startup_errors = _verify_startup_prerequisites()
    for err in startup_errors:
        logger.error("Startup validation: %s", err)
    if startup_errors:
        logger.critical("Critical startup failures detected — aborting startup")
        raise ConfigurationError(
            f"Startup failed with {len(startup_errors)} prerequisite error(s): "
            + "; ".join(startup_errors)
        )
    logger.info(
        "Startup validation complete — %d prerequisite(s) verified",
        len(startup_errors),
        extra={"structured": {"event": "startup_complete"}},
    )

    import time as _time
    import predict as _predict_mod
    _warmup_start = _time.perf_counter()
    try:
        _predict_mod.predict("warmup")
        _warmup_elapsed = (_time.perf_counter() - _warmup_start) * 1000
        logger.info("Model warmup complete — %.1fms", _warmup_elapsed)
    except Exception as _warmup_err:
        logger.warning("Model warmup failed: %s", _warmup_err)

    try:
        from services.orchestrator import analyze_text as _warmup_analyze
        _pipeline_start = _time.perf_counter()
        _warmup_analyze("warmup message to initialize pipeline components")
        _pipeline_elapsed = (_time.perf_counter() - _pipeline_start) * 1000
        logger.info("Pipeline warmup complete — %.1fms", _pipeline_elapsed)
    except Exception as _pipeline_warmup_err:
        logger.warning("Pipeline warmup failed: %s", _pipeline_warmup_err)
    registered = [getattr(r, "path", str(getattr(r, "paths", ""))) for r in app.routes]
    logger.info(
        "Registered routes: %s",
        registered,
        extra={"structured": {"event": "routes_registered", "routes": registered}},
    )

    yield

    logger.info(
        "Wary API shutting down — flushing logs and releasing resources",
        extra={"structured": {"event": "shutdown"}},
    )
    logger.info(
        "Metrics snapshot at shutdown: total_requests=%d, failures=%d",
        metrics.total_requests,
        metrics.failed_requests,
        extra={"structured": {"event": "shutdown_metrics"}},
    )

    from ocr import shutdown_ocr_pool
    try:
        shutdown_ocr_pool()
    except Exception:
        logger.warning("OCR pool shutdown encountered an error")

    try:
        from connectors.manager import shutdown_connector_pool
        shutdown_connector_pool()
    except Exception:
        logger.warning("Connector pool shutdown encountered an error")

    import logging
    logging.shutdown()


app = FastAPI(
    title="Wary API",
    description="AI-powered scam message detection engine. Combines machine learning classification with heuristic rule analysis to detect phishing, fraud, and scam SMS messages.",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

cors_origins = settings.CORS_ORIGINS
is_wildcard = cors_origins == ["*"]
if is_wildcard:
    logger.warning("CORS configured with wildcard origin — credentials disabled")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else cors_origins,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Admin-Key"],
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    SlidingWindowRateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)
app.add_middleware(
    RequestBodySizeMiddleware,
    max_body_size=settings.MAX_REQUEST_BODY_SIZE,
)

app.add_middleware(JSONStructureValidator)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=30.0)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    import time
    start = time.monotonic()
    response = await call_next(request)
    duration = time.monotonic() - start
    record_prometheus_request(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration,
    )
    return response


app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(auth_router)


@app.get("/version")
def version() -> dict:
    return {
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", get_request_id())
    err_type = type(exc).__name__
    err_msg = str(exc)
    masked = _mask_pii(err_msg)
    logger.warning(
        "%s: %s",
        err_type,
        masked,
        extra={"structured": {"request_id": request_id, "error_type": err_type}},
    )
    return JSONResponse(status_code=400, content={"detail": masked})


@app.exception_handler(ConfigurationError)
async def configuration_exception_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
    logger.critical(
        "Configuration error: %s",
        str(exc),
        extra={"structured": {"error_type": "ConfigurationError"}},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Service configuration error — check logs"},
    )


@app.exception_handler(ScamShieldError)
async def scamshield_exception_handler(request: Request, exc: ScamShieldError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", get_request_id())
    err_type = type(exc).__name__
    logger.error(
        "%s: %s",
        err_type,
        _mask_pii(str(exc)),
        extra={"structured": {"request_id": request_id, "error_type": err_type}},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", get_request_id())
    metrics.record_auth_failure()
    logger.warning(
        "Authentication failed: %s",
        str(exc),
        extra={"structured": {"request_id": request_id, "error_type": "AuthenticationError"}},
    )
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", get_request_id())
    err_type = type(exc).__name__
    logger.error(
        "Unhandled %s on %s %s",
        err_type,
        request.method,
        request.url.path,
        extra={"structured": {"request_id": request_id, "error_type": err_type}},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/metrics")
def get_metrics(request: Request):
    accept = request.headers.get("accept", "")
    if "application/json" in accept or "text/plain" not in accept:
        return metrics.snapshot()
    body, content_type = get_prometheus_metrics_endpoint()
    from fastapi.responses import Response
    return Response(content=body, media_type=content_type)
