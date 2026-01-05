"""Main application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.exceptions import AppException
from app.api.routes import router
from app.api.error_handlers import (
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"in {settings.environment} mode"
    )

    # Import close_db for cleanup
    from app.core.database import close_db

    yield

    # Shutdown
    logger.info("Shutting down application")
    logger.info("Closing database connections...")
    await close_db()
    logger.info("Database connections closed")


def create_application() -> FastAPI:
    """
    Application factory pattern.

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Convert natural language job search queries into optimized Google search queries",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Register routes
    app.include_router(router, tags=["Query Formatter"])

    # Register exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
