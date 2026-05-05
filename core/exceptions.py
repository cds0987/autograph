"""Custom package exceptions."""


class AutoGraphError(Exception):
    """Base package error."""


class DataValidationError(AutoGraphError):
    """Raised when input data cannot be normalized into records."""


class UnsupportedFormatError(AutoGraphError):
    """Raised when a file format is not supported."""


class ConfigurationError(AutoGraphError):
    """Raised for invalid runtime configuration."""


class IntegrationUnavailableError(AutoGraphError):
    """Raised when an optional dependency or service is unavailable."""
