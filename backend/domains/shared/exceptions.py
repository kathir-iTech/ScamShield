from core.exceptions import (
    ScamShieldError,
    ConfigurationError,
    ModelLoadError,
    ValidationError,
    EmptyTextError,
    TextTooLongError,
    InvalidImageError,
    ImageExtractionError,
    OCRProcessingError,
    ServiceError,
    MLServiceError,
    RulesServiceError,
    IntelServiceError,
    EvidenceServiceError,
    AssessmentError,
    ReportError,
    FileAccessError,
    DatasetNotFoundError,
    PathTraversalError,
    TextTooLargeError,
    UnicodeNormalizationError,
    ImageDecompressionBombError,
    ImageDimensionError,
    ImageCorruptedError,
    PipelineStageError,
    InputSanitisationError,
)


class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass
