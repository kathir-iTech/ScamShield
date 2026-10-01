import hashlib
import json
import os
import re
import tempfile
import time

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from PIL import Image

from config import settings
from core.auth import AuthenticatedUser, require_admin, require_auth_if_enabled
from core.context import get_request_id
from core.exceptions import (
    EmptyTextError,
    ImageCorruptedError,
    ImageDecompressionBombError,
    ImageDimensionError,
    ImageExtractionError,
    InvalidImageError,
    ValidationError,
)
from core.logger import logger
from core.metrics import metrics
from core.prediction_logger import log_prediction
from predict import get_model_info
from schemas.requests import TextAnalysisRequest, InvestigationRequest
from schemas.responses import (
    AnalysisResponse,
    ImageAnalysisResponse,
    InvestigationResponse,
    InvestigationArtefactResult,
    CampaignResult,
    TimelineEvent,
    RelationshipGraph,
    GlobalAssessment,
)
from services.orchestrator import analyze_text, PipelineError
from domains.investigation.public import investigate
from domains.knowledge.public import enrich_investigation_result
from ocr import extract_text_async
from utils.validate import sanitise_text
from config.settings import MAX_FILE_SIZE_MB, SUPPORTED_IMAGE_TYPES
from config.settings import OCR_MAX_IMAGE_DIMENSION

router = APIRouter(tags=["Analysis"])

_MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
_MAX_IMAGE_DIMENSION = OCR_MAX_IMAGE_DIMENSION
_FILENAME_SANITISE_RE = re.compile(r"[^\w.\-]")
_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

_USER_RATE_LIMIT: int = 60
_USER_RATE_WINDOW: int = 60
_USER_RATE_BLOCK_SECONDS: int = 60


def _sanitise_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename or "upload.png")
    safe_name = _FILENAME_SANITISE_RE.sub("_", name)[:64]
    safe_ext = ext if ext.lower() in _ALLOWED_EXTENSIONS else ".png"
    return f"{safe_name}{safe_ext}"


def _enforce_user_rate_limit(http_request: Request, user: AuthenticatedUser) -> None:
    if not settings.AUTH_ENABLED or not user.is_authenticated or not user.id:
        return
    bucket = f"analyze:user:{user.id}"
    try:
        from core.storage.repositories import RateLimitRepo

        state = RateLimitRepo().hit(
            bucket, _USER_RATE_WINDOW, _USER_RATE_LIMIT, _USER_RATE_BLOCK_SECONDS
        )
    except Exception as exc:
        logger.debug("Per-user rate limit unavailable: %s", exc)
        return
    if state["allowed"]:
        return
    retry_after = int(float(state.get("blocked_until", 0.0)) - time.time())
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many analysis requests. Please try again later.",
        headers={
            "Retry-After": str(retry_after if retry_after > 0 else _USER_RATE_WINDOW),
            "X-RateLimit-Limit": str(_USER_RATE_LIMIT),
            "X-RateLimit-Remaining": "0",
        },
    )


def _persist_analysis(
    request_id: str,
    user_id: str,
    source: str,
    text: str,
    result: dict,
    duration_ms: float,
) -> str:
    try:
        from core.storage.repositories import AnalysisRepo

        model_version = "unknown"
        try:
            model_version = str(get_model_info().get("version", "unknown"))
        except Exception:
            pass

        prediction = str(result.get("prediction", "") or "")
        confidence = float(result.get("confidence", 0.0) or 0.0)
        category = str(result.get("scam_category", "") or "")
        risk_level = str(result.get("risk_level", "") or "")
        preview = (text or "")[:120]

        return AnalysisRepo().insert(
            {
                "request_id": request_id,
                "user_id": user_id or "",
                "source": source,
                "input_hash": hashlib.sha256((text or "").encode("utf-8")).hexdigest(),
                "input_preview": preview,
                "prediction": prediction,
                "is_scam": 1 if prediction == "scam" else 0,
                "confidence": confidence,
                "risk_level": risk_level,
                "category": category,
                "model_version": model_version,
                "duration_ms": float(duration_ms),
                "payload": json.dumps(
                    {
                        "prediction": prediction,
                        "confidence": confidence,
                        "category": category,
                        "source": source,
                    },
                    default=str,
                ),
                "created_at": time.time(),
            }
        )
    except Exception as exc:
        logger.warning(
            "Analysis persistence skipped: %s",
            exc,
            extra={"structured": {"event": "analysis_persist_failed", "request_id": request_id}},
        )
        return ""


@router.post("/analyze/text", response_model=AnalysisResponse)
def analyze_text_endpoint(
    body: TextAnalysisRequest,
    http_request: Request,
    user: AuthenticatedUser = Depends(require_auth_if_enabled),
) -> AnalysisResponse:
    start = time.perf_counter()
    rid = get_request_id()
    _enforce_user_rate_limit(http_request, user)
    try:
        text = sanitise_text(body.text)
        logger.info(
            "Analyzing text message (%d chars)",
            len(text),
            extra={"structured": {"request_id": rid, "char_count": len(text)}},
        )
        result = analyze_text(text)
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=True, is_ocr=False, is_validation_failure=False)
        _persist_analysis(rid, user.id, "text", text, result, elapsed)
        try:
            model_info = get_model_info()
            log_prediction(
                request_id=rid,
                text=text,
                prediction=result.get("prediction", "unknown"),
                confidence=result.get("confidence", 0.0),
                model_version=model_info.get("version", "unknown"),
                latency_ms=elapsed,
                category=result.get("scam_category"),
            )
        except Exception:
            logger.warning("Failed to log prediction", exc_info=True)
        return AnalysisResponse(**result)
    except ValidationError:
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=False, is_ocr=False, is_validation_failure=True)
        raise
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=False, is_ocr=False, is_validation_failure=False)
        raise


@router.post("/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(
    http_request: Request,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(require_auth_if_enabled),
) -> ImageAnalysisResponse:
    start = time.perf_counter()
    rid = get_request_id()
    _enforce_user_rate_limit(http_request, user)
    try:
        file.filename = _sanitise_filename(file.filename or "upload.png")

        if not file.content_type or not file.content_type.startswith("image/"):
            raise InvalidImageError("File must be an image")
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise InvalidImageError(
                f"Unsupported image type '{file.content_type}'. "
                f"Supported: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )

        contents = await file.read()
        if len(contents) == 0:
            raise InvalidImageError("Uploaded file is empty")
        if len(contents) > _MAX_FILE_SIZE_BYTES:
            raise InvalidImageError(
                f"File exceeds maximum size of {MAX_FILE_SIZE_MB} MB "
                f"(got {len(contents) / 1024 / 1024:.1f} MB)"
            )

        suffix = os.path.splitext(file.filename or "upload.png")[1] or ".png"
        safe_suffix = suffix if suffix.lower() in _ALLOWED_EXTENSIONS else ".png"

        temp_path: str = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=safe_suffix) as tmp:
                tmp.write(contents)
                temp_path = tmp.name

            with Image.open(temp_path) as img:
                width, height = img.size
                if width > _MAX_IMAGE_DIMENSION or height > _MAX_IMAGE_DIMENSION:
                    raise ImageDimensionError(
                        f"Image dimensions ({width}x{height}) exceed maximum "
                        f"({_MAX_IMAGE_DIMENSION}x{_MAX_IMAGE_DIMENSION})"
                    )

            ocr_start = time.perf_counter()
            extracted = await extract_text_async(temp_path)
            ocr_elapsed = (time.perf_counter() - ocr_start) * 1000
            metrics.record_stage("OCR", ocr_elapsed)
        except (ImageCorruptedError, ImageDecompressionBombError, ImageDimensionError):
            raise
        except Exception as exc:
            logger.error(
                "OCR extraction failed: %s",
                exc,
                extra={"structured": {"request_id": rid}},
            )
            raise ImageExtractionError("Failed to extract text from image") from exc
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        extracted = extracted.strip()
        if not extracted:
            raise ImageExtractionError("No text could be extracted from the image")

        try:
            extracted = sanitise_text(extracted)
        except EmptyTextError:
            raise ImageExtractionError("No valid text could be extracted from the image")

        logger.info(
            "Analyzing image text (%d chars)",
            len(extracted),
            extra={"structured": {"request_id": rid}},
        )
        result = analyze_text(extracted)
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=True, is_ocr=True, is_validation_failure=False)
        _persist_analysis(rid, user.id, "image", extracted, result, elapsed)
        try:
            model_info = get_model_info()
            log_prediction(
                request_id=rid,
                text=extracted,
                prediction=result.get("prediction", "unknown"),
                confidence=result.get("confidence", 0.0),
                model_version=model_info.get("version", "unknown"),
                latency_ms=elapsed,
                category=result.get("scam_category"),
            )
        except Exception:
            logger.warning("Failed to log prediction", exc_info=True)
        return ImageAnalysisResponse(extracted_text=extracted, **result)
    except (InvalidImageError, ImageExtractionError):
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=False, is_ocr=True, is_validation_failure=True)
        raise
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=False, is_ocr=True, is_validation_failure=False)
        raise


@router.post("/analyze/investigation", response_model=InvestigationResponse)
def investigate_endpoint(
    request: InvestigationRequest,
    admin: AuthenticatedUser = Depends(require_admin),
) -> InvestigationResponse:
    start = time.perf_counter()
    rid = get_request_id()
    try:
        result = investigate(request.artefacts)
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=True, is_ocr=False, is_validation_failure=False)

        artefact_results = [
            InvestigationArtefactResult(**a) for a in result.artefact_summaries
        ]
        campaign = CampaignResult(
            campaign_detected=result.campaign.get("campaign_detected", False),
            confidence=result.campaign.get("confidence", 0.0),
            indicators=result.campaign.get("indicators", {}),
            summary=result.campaign.get("summary", ""),
        )
        timeline = [
            TimelineEvent(**ev) for ev in result.timeline
        ]
        graph = RelationshipGraph(
            nodes=result.relationship_graph.get("nodes", []),
            edges=result.relationship_graph.get("edges", []),
        )
        assessment = GlobalAssessment(
            overall_risk=result.global_risk.get("overall_risk", "UNKNOWN"),
            overall_score=result.global_risk.get("overall_score", 0),
            confidence=result.global_risk.get("confidence", 0.0),
            dominant_family=result.global_risk.get("dominant_family", ""),
            peak_single_score=result.global_risk.get("peak_single_score", 0),
            average_score=result.global_risk.get("average_score", 0.0),
            highest_risk_artefact=result.global_risk.get("highest_risk_artefact", -1),
            strongest_evidence=result.global_risk.get("strongest_evidence", []),
            weakest_signals=result.global_risk.get("weakest_signals", []),
            open_questions=result.global_risk.get("open_questions", []),
        )

        enrichment = enrich_investigation_result(
            result.merged_entities,
            result.repeated_indicators,
            result.global_risk.get("dominant_family", ""),
        )
        ireport = result.investigation_report
        if isinstance(ireport, dict):
            ireport["knowledge_enrichment"] = {
                "knowledge_matches": enrichment.get("knowledge_matches", []),
                "advisory_references": enrichment.get("advisory_references", []),
                "historical_matches": enrichment.get("historical_matches", []),
            }

        return InvestigationResponse(
            investigation_id=result.investigation_id,
            artefacts_analysed=result.artefacts_analysed,
            artefact_results=artefact_results,
            merged_entities=result.merged_entities,
            repeated_indicators=result.repeated_indicators,
            campaign=campaign,
            timeline=timeline,
            relationship_graph=graph,
            global_assessment=assessment,
            investigation_report=ireport,
            knowledge_matches=enrichment.get("knowledge_matches", []),
            advisory_references=enrichment.get("advisory_references", []),
            historical_matches=enrichment.get("historical_matches", []),
        )
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=False, is_ocr=False, is_validation_failure=False)
        raise
