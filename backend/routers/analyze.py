import os
import re
import tempfile
import time

from fastapi import APIRouter, Depends, File, UploadFile
from PIL import Image

from core.auth import AuthenticatedUser, require_admin
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
from ocr import extract_text
from utils.validate import sanitise_text
from config.settings import MAX_FILE_SIZE_MB, SUPPORTED_IMAGE_TYPES

router = APIRouter(tags=["Analysis"])

_MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
_MAX_IMAGE_DIMENSION = 8000
_FILENAME_SANITISE_RE = re.compile(r"[^\w.\-]")
_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _sanitise_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename or "upload.png")
    safe_name = _FILENAME_SANITISE_RE.sub("_", name)[:64]
    safe_ext = ext if ext.lower() in _ALLOWED_EXTENSIONS else ".png"
    return f"{safe_name}{safe_ext}"


@router.post("/analyze/text", response_model=AnalysisResponse)
def analyze_text_endpoint(request: TextAnalysisRequest) -> AnalysisResponse:
    start = time.perf_counter()
    rid = get_request_id()
    try:
        text = sanitise_text(request.text)
        logger.info(
            "Analyzing text message (%d chars)",
            len(text),
            extra={"structured": {"request_id": rid, "char_count": len(text)}},
        )
        result = analyze_text(text)
        elapsed = (time.perf_counter() - start) * 1000
        metrics.record_request(elapsed, success=True, is_ocr=False, is_validation_failure=False)
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
async def analyze_image_endpoint(file: UploadFile = File(...)) -> ImageAnalysisResponse:
    start = time.perf_counter()
    rid = get_request_id()
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
            extracted = extract_text(temp_path)
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
