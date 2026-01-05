"""Global exception handlers for the API."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.core.exceptions import (
    AppException,
    OpenAIServiceError,
    InvalidQueryError,
    RateLimitExceededError
)
from app.models.schemas import ErrorResponse

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.

    Args:
        request: FastAPI request
        exc: Application exception

    Returns:
        JSON error response
    """
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )

    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON error response
    """
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )

    error_response = ErrorResponse(
        error="ValidationError",
        message="Request validation failed",
        detail=str(exc.errors()),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Generic exception

    Returns:
        JSON error response
    """
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )

    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        detail=str(exc) if logger.level == logging.DEBUG else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )
