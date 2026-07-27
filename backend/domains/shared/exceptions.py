class ScamShieldError(Exception):
    """Base exception for all ScamShield errors."""


class ConfigurationError(ScamShieldError):
    """Raised when required configuration is missing or invalid."""


class ModelLoadError(ConfigurationError):
    """Raised when the ML model fails to load."""


class ValidationError(ScamShieldError):
    """Raised when input validation fails."""


class EmptyTextError(ValidationError):
    """Raised when input text is empty after stripping."""


class TextTooLongError(ValidationError):
    """Raised when input text exceeds maximum length."""


class InvalidImageError(ValidationError):
    """Raised when the uploaded file is not a valid image."""


class ImageExtractionError(ScamShieldError):
    """Raised when text extraction from an image fails."""


class OCRProcessingError(ImageExtractionError):
    """Raised when the OCR engine fails to process an image."""


class ServiceError(ScamShieldError):
    """Base exception for service-level errors."""


class MLServiceError(ServiceError):
    """Raised when the ML prediction service fails."""


class RulesServiceError(ServiceError):
    """Raised when the rules engine service fails."""


class IntelServiceError(ServiceError):
    """Raised when the threat intelligence service fails."""


class EvidenceServiceError(ServiceError):
    """Raised when the evidence building service fails."""


class AssessmentError(ServiceError):
    """Raised when the assessment service fails."""


class ReportError(ServiceError):
    """Raised when the report generation service fails."""


class FileAccessError(ScamShieldError):
    """Raised when a required file cannot be read or written."""


class DatasetNotFoundError(FileAccessError):
    """Raised when the training dataset is missing."""


class PathTraversalError(ValidationError):
    """Raised when a file path contains traversal sequences."""


class TextTooLargeError(ValidationError):
    """Raised when input text exceeds the maximum allowed length."""


class UnicodeNormalizationError(ValidationError):
    """Raised when text contains invalid unicode sequences."""


class ImageDecompressionBombError(ValidationError):
    """Raised when an image exceeds the maximum allowed pixel count."""


class ImageDimensionError(ValidationError):
    """Raised when image dimensions exceed the maximum allowed."""


class ImageCorruptedError(ValidationError):
    """Raised when the image file is corrupted or unreadable."""


class PipelineStageError(ServiceError):
    """Raised when a non-critical pipeline stage fails; the stage is skipped."""


class InputSanitisationError(ValidationError):
    """Raised when input contains prohibited content after sanitisation."""


class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass
