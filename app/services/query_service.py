"""Service for managing query history operations."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import QueryHistory


class QueryService:
    """Service for query history database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the query service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_query_history(
        self,
        original_query: str,
        query_string: str,
        locations: Optional[List[str]] = None,
        duration_from: Optional[str] = None,
        duration_to: Optional[str] = None,
        formatted_query: Optional[str] = None,
        last_run_at: Optional[datetime] = None
    ) -> QueryHistory:
        """
        Create a new query history record.

        Args:
            original_query: The original user query
            query_string: The formatted search query string
            locations: List of extracted locations
            duration_from: Start date in DD/MM/YYYY format
            duration_to: End date in DD/MM/YYYY format
            formatted_query: Legacy formatted query (for backwards compatibility)
            last_run_at: When the query was last run (defaults to now)

        Returns:
            QueryHistory: The created query history record
        """
        if last_run_at is None:
            last_run_at = datetime.utcnow()

        if locations is None:
            locations = []

        query_history = QueryHistory(
            original_query=original_query,
            query_string=query_string,
            locations=locations,
            duration_from=duration_from,
            duration_to=duration_to,
            formatted_query=formatted_query or query_string,
            last_run_at=last_run_at
        )

        self.db.add(query_history)
        await self.db.flush()
        await self.db.refresh(query_history)

        return query_history

    async def get_query_history_by_id(self, query_id: int) -> Optional[QueryHistory]:
        """
        Get a query history record by ID.

        Args:
            query_id: The query history ID

        Returns:
            QueryHistory or None if not found
        """
        result = await self.db.execute(
            select(QueryHistory).where(QueryHistory.id == query_id)
        )
        return result.scalar_one_or_none()

    async def get_all_query_history(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[QueryHistory]:
        """
        Get all query history records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of QueryHistory records
        """
        result = await self.db.execute(
            select(QueryHistory)
            .order_by(QueryHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_run_at(
        self,
        query_id: int,
        last_run_at: Optional[datetime] = None
    ) -> Optional[QueryHistory]:
        """
        Update the last_run_at timestamp for a query.

        Args:
            query_id: The query history ID
            last_run_at: When the query was last run (defaults to now)

        Returns:
            Updated QueryHistory or None if not found
        """
        query_history = await self.get_query_history_by_id(query_id)

        if query_history:
            if last_run_at is None:
                last_run_at = datetime.utcnow()

            query_history.last_run_at = last_run_at
            await self.db.flush()
            await self.db.refresh(query_history)

        return query_history
