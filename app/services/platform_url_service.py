"""Service for managing platform URL operations."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import PlatformURL


class PlatformURLService:
    """Service for platform URL database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the platform URL service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_platform_url(
        self,
        platform: str,
        url: str,
        status: int = 1
    ) -> PlatformURL:
        """
        Create a new platform URL record.

        Args:
            platform: Platform name
            url: Platform URL
            status: Status (0 = inactive, 1 = active)

        Returns:
            PlatformURL: The created platform URL record
        """
        platform_url = PlatformURL(
            platform=platform,
            url=url,
            status=status
        )

        self.db.add(platform_url)
        await self.db.flush()
        await self.db.refresh(platform_url)

        return platform_url

    async def get_platform_url_by_id(
        self,
        platform_url_id: int,
        include_deleted: bool = False
    ) -> Optional[PlatformURL]:
        """
        Get a platform URL record by ID.

        Args:
            platform_url_id: The platform URL ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            PlatformURL or None if not found
        """
        query = select(PlatformURL).where(PlatformURL.id == platform_url_id)

        if not include_deleted:
            query = query.where(PlatformURL.deleted_at == None)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_platform_urls(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[PlatformURL]:
        """
        Get all platform URL records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of PlatformURL records
        """
        query = select(PlatformURL)

        if not include_deleted:
            query = query.where(PlatformURL.deleted_at == None)

        query = query.order_by(PlatformURL.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_platform_url(
        self,
        platform_url_id: int,
        platform: Optional[str] = None,
        url: Optional[str] = None,
        status: Optional[int] = None
    ) -> Optional[PlatformURL]:
        """
        Update a platform URL record.

        Args:
            platform_url_id: The platform URL ID
            platform: New platform name (optional)
            url: New URL (optional)
            status: New status (optional)

        Returns:
            Updated PlatformURL or None if not found
        """
        platform_url = await self.get_platform_url_by_id(platform_url_id)

        if platform_url:
            if platform is not None:
                platform_url.platform = platform
            if url is not None:
                platform_url.url = url
            if status is not None:
                platform_url.status = status

            await self.db.flush()
            await self.db.refresh(platform_url)

        return platform_url

    async def delete_platform_url(self, platform_url_id: int) -> Optional[PlatformURL]:
        """
        Soft delete a platform URL record.

        Args:
            platform_url_id: The platform URL ID

        Returns:
            Deleted PlatformURL or None if not found
        """
        platform_url = await self.get_platform_url_by_id(platform_url_id)

        if platform_url:
            platform_url.deleted_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(platform_url)

        return platform_url
