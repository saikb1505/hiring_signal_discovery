"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for application-specific errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OpenAIServiceError(AppException):
    """Exception raised when OpenAI API calls fail."""

    def __init__(self, message: str = "OpenAI service error"):
        super().__init__(message, status_code=502)


class InvalidQueryError(AppException):
    """Exception raised when query validation fails."""

    def __init__(self, message: str = "Invalid query provided"):
        super().__init__(message, status_code=400)


class RateLimitExceededError(AppException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class ConfigurationError(AppException):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status_code=500)


class SerperServiceError(AppException):
    """Exception raised when SerperAPI calls fail."""

    def __init__(self, message: str = "SerperAPI service error"):
        super().__init__(message, status_code=502)
