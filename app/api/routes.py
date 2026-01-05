"""API route handlers."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    SearchQueryRequest,
    FormattedQueryResponse,
    HealthResponse,
    PlatformURLCreate,
    PlatformURLUpdate,
    PlatformURLResponse
)
from app.services.openai_service import OpenAIService
from app.services.query_service import QueryService
from app.services.platform_url_service import PlatformURLService
from app.api.dependencies import get_cached_openai_service
from app.core.config import Settings, get_settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/format-query",
    response_model=FormattedQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Format job search query",
    description="Convert a natural language job search query into an optimized Google search query",
    responses={
        200: {
            "description": "Query formatted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "original_query": "Senior software engineer in Hyderabad last 1 week",
                        "query_string": '("senior software engineer" OR "senior developer" OR "senior sde") after:2025-12-18 before:2025-12-25',
                        "locations": ["Hyderabad", "Bangalore"],
                        "duration": {
                            "from": "18/12/2025",
                            "to": "25/12/2025"
                        },
                        "metadata": {
                            "model": "gpt-4o-mini",
                            "tokens_used": 245
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid query"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "OpenAI service error"}
    }
)
async def format_search_query(
    request: SearchQueryRequest,
    openai_service: OpenAIService = Depends(get_cached_openai_service),
    db: AsyncSession = Depends(get_db)
) -> FormattedQueryResponse:
    """
    Format a natural language job search query.

    Args:
        request: Search query request
        openai_service: OpenAI service instance

    Returns:
        Formatted query response
    """
    logger.info(f"Received format request for query: {request.query[:100]}...")

    formatted_query_data, metadata = await openai_service.format_query(request.query)
    breakpoint()
    # Save query to database
    query_service = QueryService(db)
    await query_service.create_query_history(
        original_query=request.query,
        query_string=formatted_query_data.get("query_string", ""),
        locations=formatted_query_data.get("locations", []),
        duration_from=formatted_query_data.get("duration", {}).get("from", ""),
        duration_to=formatted_query_data.get("duration", {}).get("to", "")
    )
    logger.info("Query saved to database")

    return FormattedQueryResponse(
        original_query=request.query,
        query_string=formatted_query_data.get("query_string", ""),
        locations=formatted_query_data.get("locations", []),
        duration={
            "from": formatted_query_data.get("duration", {}).get("from", ""),
            "to": formatted_query_data.get("duration", {}).get("to", "")
        },
        metadata=metadata
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the service is healthy and running"
)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """
    Health check endpoint.

    Args:
        settings: Application settings

    Returns:
        Health status
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment
    )


@router.get(
    "/",
    summary="API information",
    description="Get information about the API and available endpoints"
)
async def root(settings: Settings = Depends(get_settings)) -> dict:
    """
    Root endpoint with API information.

    Args:
        settings: Application settings

    Returns:
        API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "/format-query": "POST - Format a natural language job search query",
            "/health": "GET - Health check endpoint",
            "/platform-urls": "GET - Get all platform URLs",
            "/platform-urls/{id}": "GET - Get platform URL by ID",
            "/platform-urls": "POST - Create a new platform URL",
            "/platform-urls/{id}": "PUT - Update a platform URL",
            "/platform-urls/{id}": "DELETE - Soft delete a platform URL",
            "/docs": "GET - Interactive API documentation (Swagger UI)",
            "/redoc": "GET - Alternative API documentation (ReDoc)"
        }
    }


@router.post(
    "/platform-urls",
    response_model=PlatformURLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new platform URL",
    description="Create a new platform URL entry with platform name and URL"
)
async def create_platform_url(
    request: PlatformURLCreate,
    db: AsyncSession = Depends(get_db)
) -> PlatformURLResponse:
    """
    Create a new platform URL.

    Args:
        request: Platform URL creation request
        db: Database session

    Returns:
        Created platform URL
    """
    logger.info(f"Creating platform URL for platform: {request.platform}")

    platform_url_service = PlatformURLService(db)
    platform_url = await platform_url_service.create_platform_url(
        platform=request.platform,
        url=request.url,
        status=request.status
    )

    logger.info(f"Platform URL created with ID: {platform_url.id}")

    return PlatformURLResponse(
        id=platform_url.id,
        platform=platform_url.platform,
        url=platform_url.url,
        status=platform_url.status,
        created_at=platform_url.created_at.isoformat(),
        updated_at=platform_url.updated_at.isoformat()
    )


@router.get(
    "/platform-urls",
    response_model=list[PlatformURLResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all platform URLs",
    description="Retrieve all platform URLs with pagination support"
)
async def get_all_platform_urls(
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db)
) -> list[PlatformURLResponse]:
    """
    Get all platform URLs.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_deleted: Whether to include soft-deleted records
        db: Database session

    Returns:
        List of platform URLs
    """
    logger.info(f"Fetching platform URLs (skip={skip}, limit={limit}, include_deleted={include_deleted})")

    platform_url_service = PlatformURLService(db)
    platform_urls = await platform_url_service.get_all_platform_urls(
        skip=skip,
        limit=limit,
        include_deleted=include_deleted
    )

    return [
        PlatformURLResponse(
            id=p.id,
            platform=p.platform,
            url=p.url,
            status=p.status,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat()
        )
        for p in platform_urls
    ]


@router.get(
    "/platform-urls/{platform_url_id}",
    response_model=PlatformURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Get platform URL by ID",
    description="Retrieve a specific platform URL by its ID"
)
async def get_platform_url(
    platform_url_id: int,
    db: AsyncSession = Depends(get_db)
) -> PlatformURLResponse:
    """
    Get a platform URL by ID.

    Args:
        platform_url_id: Platform URL ID
        db: Database session

    Returns:
        Platform URL details
    """
    logger.info(f"Fetching platform URL with ID: {platform_url_id}")

    platform_url_service = PlatformURLService(db)
    platform_url = await platform_url_service.get_platform_url_by_id(platform_url_id)

    if not platform_url:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform URL with ID {platform_url_id} not found"
        )

    return PlatformURLResponse(
        id=platform_url.id,
        platform=platform_url.platform,
        url=platform_url.url,
        status=platform_url.status,
        created_at=platform_url.created_at.isoformat(),
        updated_at=platform_url.updated_at.isoformat()
    )


@router.put(
    "/platform-urls/{platform_url_id}",
    response_model=PlatformURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Update platform URL",
    description="Update an existing platform URL"
)
async def update_platform_url(
    platform_url_id: int,
    request: PlatformURLUpdate,
    db: AsyncSession = Depends(get_db)
) -> PlatformURLResponse:
    """
    Update a platform URL.

    Args:
        platform_url_id: Platform URL ID
        request: Platform URL update request
        db: Database session

    Returns:
        Updated platform URL
    """
    logger.info(f"Updating platform URL with ID: {platform_url_id}")

    platform_url_service = PlatformURLService(db)
    platform_url = await platform_url_service.update_platform_url(
        platform_url_id=platform_url_id,
        platform=request.platform,
        url=request.url,
        status=request.status
    )

    if not platform_url:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform URL with ID {platform_url_id} not found"
        )

    logger.info(f"Platform URL {platform_url_id} updated successfully")

    return PlatformURLResponse(
        id=platform_url.id,
        platform=platform_url.platform,
        url=platform_url.url,
        status=platform_url.status,
        created_at=platform_url.created_at.isoformat(),
        updated_at=platform_url.updated_at.isoformat()
    )


@router.delete(
    "/platform-urls/{platform_url_id}",
    response_model=PlatformURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete platform URL",
    description="Soft delete a platform URL (sets deleted_at timestamp)"
)
async def delete_platform_url(
    platform_url_id: int,
    db: AsyncSession = Depends(get_db)
) -> PlatformURLResponse:
    """
    Soft delete a platform URL.

    Args:
        platform_url_id: Platform URL ID
        db: Database session

    Returns:
        Deleted platform URL
    """
    logger.info(f"Deleting platform URL with ID: {platform_url_id}")

    platform_url_service = PlatformURLService(db)
    platform_url = await platform_url_service.delete_platform_url(platform_url_id)

    if not platform_url:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform URL with ID {platform_url_id} not found"
        )

    logger.info(f"Platform URL {platform_url_id} deleted successfully")

    return PlatformURLResponse(
        id=platform_url.id,
        platform=platform_url.platform,
        url=platform_url.url,
        status=platform_url.status,
        created_at=platform_url.created_at.isoformat(),
        updated_at=platform_url.updated_at.isoformat()
    )
