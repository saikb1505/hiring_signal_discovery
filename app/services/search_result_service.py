"""Service for managing search result operations."""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import SearchResult


class SearchResultService:
    """Service for search result database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the search result service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_search_result(
        self,
        query_history_id: int,
        platform_id: Optional[int],
        search_id: Optional[str],
        position: Optional[int],
        title: str,
        link: str,
        snippet: Optional[str] = None,
        source: Optional[str] = None,
        redirect_link: Optional[str] = None,
        displayed_link: Optional[str] = None,
        favicon: Optional[str] = None,
        snippet_highlighted_words: Optional[List[str]] = None
    ) -> SearchResult:
        """
        Create a new search result record.

        Args:
            query_history_id: Foreign key to query history
            platform_id: Foreign key to platform URL
            search_id: External search ID from search API
            position: Position in search results
            title: Result title
            link: Result URL
            snippet: Result snippet/description
            source: Source of the result
            redirect_link: Redirect URL if any
            displayed_link: Displayed URL in search results
            favicon: Favicon URL
            snippet_highlighted_words: List of highlighted words in snippet

        Returns:
            SearchResult: The created search result record
        """
        search_result = SearchResult(
            query_history_id=query_history_id,
            platform_id=platform_id,
            search_id=search_id,
            position=position,
            title=title,
            link=link,
            snippet=snippet,
            source=source,
            redirect_link=redirect_link,
            displayed_link=displayed_link,
            favicon=favicon,
            snippet_highlighted_words=snippet_highlighted_words or []
        )

        self.db.add(search_result)
        await self.db.flush()
        await self.db.refresh(search_result)

        return search_result

    async def create_search_results_bulk(
        self,
        query_history_id: int,
        platform_id: Optional[int],
        search_id: Optional[str],
        results: List[Dict[str, Any]]
    ) -> List[SearchResult]:
        """
        Create multiple search result records in bulk.

        Args:
            query_history_id: Foreign key to query history
            platform_id: Foreign key to platform URL
            search_id: External search ID from search API
            results: List of result dictionaries from search API

        Returns:
            List[SearchResult]: List of created search result records
        """
        search_results = []

        for result in results:
            search_result = SearchResult(
                query_history_id=query_history_id,
                platform_id=platform_id,
                search_id=search_id,
                position=result.get("position"),
                title=result.get("title", ""),
                link=result.get("link", ""),
                snippet=result.get("snippet"),
                source=result.get("source"),
                redirect_link=result.get("redirect_link"),
                displayed_link=result.get("displayed_link"),
                favicon=result.get("favicon"),
                snippet_highlighted_words=result.get("snippet_highlighted_words", [])
            )
            search_results.append(search_result)

        self.db.add_all(search_results)
        await self.db.flush()

        # Refresh all objects
        for search_result in search_results:
            await self.db.refresh(search_result)

        return search_results

    async def get_search_result_by_id(self, result_id: int) -> Optional[SearchResult]:
        """
        Get a search result record by ID.

        Args:
            result_id: The search result ID

        Returns:
            SearchResult or None if not found
        """
        result = await self.db.execute(
            select(SearchResult).where(SearchResult.id == result_id)
        )
        return result.scalar_one_or_none()

    async def get_search_results_by_query_history_id(
        self,
        query_history_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SearchResult]:
        """
        Get all search results for a specific query history.

        Args:
            query_history_id: The query history ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of SearchResult records
        """
        result = await self.db.execute(
            select(SearchResult)
            .where(SearchResult.query_history_id == query_history_id)
            .order_by(SearchResult.position.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_search_results_by_platform_id(
        self,
        platform_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SearchResult]:
        """
        Get all search results for a specific platform.

        Args:
            platform_id: The platform ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of SearchResult records
        """
        result = await self.db.execute(
            select(SearchResult)
            .where(SearchResult.platform_id == platform_id)
            .order_by(SearchResult.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_search_results(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[SearchResult]:
        """
        Get all search results with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of SearchResult records
        """
        result = await self.db.execute(
            select(SearchResult)
            .order_by(SearchResult.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_search_result(self, result_id: int) -> Optional[SearchResult]:
        """
        Delete a search result record.

        Args:
            result_id: The search result ID

        Returns:
            Deleted SearchResult or None if not found
        """
        search_result = await self.get_search_result_by_id(result_id)

        if search_result:
            await self.db.delete(search_result)
            await self.db.flush()

        return search_result

    async def delete_search_results_by_query_history_id(
        self,
        query_history_id: int
    ) -> int:
        """
        Delete all search results for a specific query history.

        Args:
            query_history_id: The query history ID

        Returns:
            Number of deleted records
        """
        results = await self.get_search_results_by_query_history_id(
            query_history_id,
            skip=0,
            limit=10000  # Large limit to get all results
        )

        for result in results:
            await self.db.delete(result)

        await self.db.flush()

        return len(results)
