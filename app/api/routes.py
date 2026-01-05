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
    PlatformURLResponse,
    QueryHistoryResponse,
    QueryHistoryUpdate
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
    "/search_query",
    response_model=FormattedQueryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and format job search query",
    description="Convert a natural language job search query into an optimized Google search query and save to history",
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
    "/search_query",
    response_model=list[QueryHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all search queries",
    description="Retrieve all search query history with pagination support"
)
async def get_all_search_queries(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[QueryHistoryResponse]:
    """
    Get all search query history.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of query history records
    """
    logger.info(f"Fetching search queries (skip={skip}, limit={limit})")

    query_service = QueryService(db)
    queries = await query_service.get_all_query_history(skip=skip, limit=limit)

    return [
        QueryHistoryResponse(
            id=q.id,
            original_query=q.original_query,
            query_string=q.query_string,
            locations=q.locations or [],
            duration_from=q.duration_from,
            duration_to=q.duration_to,
            last_run_at=q.last_run_at.isoformat(),
            created_at=q.created_at.isoformat(),
            updated_at=q.updated_at.isoformat()
        )
        for q in queries
    ]


@router.get(
    "/search_query/{query_id}",
    response_model=QueryHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get search query by ID",
    description="Retrieve a specific search query by its ID"
)
async def get_search_query(
    query_id: int,
    db: AsyncSession = Depends(get_db)
) -> QueryHistoryResponse:
    """
    Get a search query by ID.

    Args:
        query_id: Query history ID
        db: Database session

    Returns:
        Query history details
    """
    logger.info(f"Fetching search query with ID: {query_id}")

    query_service = QueryService(db)
    query = await query_service.get_query_history_by_id(query_id)

    if not query:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search query with ID {query_id} not found"
        )

    return QueryHistoryResponse(
        id=query.id,
        original_query=query.original_query,
        query_string=query.query_string,
        locations=query.locations or [],
        duration_from=query.duration_from,
        duration_to=query.duration_to,
        last_run_at=query.last_run_at.isoformat(),
        created_at=query.created_at.isoformat(),
        updated_at=query.updated_at.isoformat()
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
            "/search_query": "POST - Create and format a natural language job search query",
            "/search_query": "GET - Get all search query history",
            "/search_query/{id}": "GET - Get search query by ID",
            "/search_query/{id}": "PUT - Update a search query",
            "/search_query/{id}": "DELETE - Delete a search query",
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


@router.put(
    "/search_query/{query_id}",
    response_model=QueryHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update search query",
    description="Update an existing search query"
)
async def update_search_query(
    query_id: int,
    request: QueryHistoryUpdate,
    db: AsyncSession = Depends(get_db)
) -> QueryHistoryResponse:
    """
    Update a search query.

    Args:
        query_id: Query history ID
        request: Query history update request
        db: Database session

    Returns:
        Updated query history
    """
    logger.info(f"Updating search query with ID: {query_id}")

    query_service = QueryService(db)
    query = await query_service.update_query_history(
        query_id=query_id,
        original_query=request.original_query,
        query_string=request.query_string,
        locations=request.locations,
        duration_from=request.duration_from,
        duration_to=request.duration_to
    )

    if not query:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search query with ID {query_id} not found"
        )

    logger.info(f"Search query {query_id} updated successfully")

    return QueryHistoryResponse(
        id=query.id,
        original_query=query.original_query,
        query_string=query.query_string,
        locations=query.locations or [],
        duration_from=query.duration_from,
        duration_to=query.duration_to,
        last_run_at=query.last_run_at.isoformat(),
        created_at=query.created_at.isoformat(),
        updated_at=query.updated_at.isoformat()
    )


@router.delete(
    "/search_query/{query_id}",
    response_model=QueryHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete search query",
    description="Delete a search query from history"
)
async def delete_search_query(
    query_id: int,
    db: AsyncSession = Depends(get_db)
) -> QueryHistoryResponse:
    """
    Delete a search query.

    Args:
        query_id: Query history ID
        db: Database session

    Returns:
        Deleted query history
    """
    logger.info(f"Deleting search query with ID: {query_id}")

    query_service = QueryService(db)
    query = await query_service.delete_query_history(query_id)

    if not query:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search query with ID {query_id} not found"
        )

    logger.info(f"Search query {query_id} deleted successfully")

    return QueryHistoryResponse(
        id=query.id,
        original_query=query.original_query,
        query_string=query.query_string,
        locations=query.locations or [],
        duration_from=query.duration_from,
        duration_to=query.duration_to,
        last_run_at=query.last_run_at.isoformat(),
        created_at=query.created_at.isoformat(),
        updated_at=query.updated_at.isoformat()
    )


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
