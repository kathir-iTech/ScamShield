class ConnectorError(Exception):
    """Base exception for all connector errors."""


class ConnectorTimeoutError(ConnectorError):
    """Raised when a connector lookup exceeds the timeout."""


class ConnectorUnavailableError(ConnectorError):
    """Raised when a connector health check fails."""


class ConnectorLookupError(ConnectorError):
    """Raised when a connector lookup fails unexpectedly."""


class ConnectorConfigError(ConnectorError):
    """Raised when a connector configuration is invalid."""
