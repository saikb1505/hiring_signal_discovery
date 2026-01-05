"""Database models using SQLAlchemy ORM."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class QueryHistory(Base):
    """Model for storing query search history."""

    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_query = Column(Text, nullable=False)
    query_string = Column(Text, nullable=False)
    locations = Column(JSON, nullable=True, default=list)
    duration_from = Column(String(10), nullable=True)  # DD/MM/YYYY format
    duration_to = Column(String(10), nullable=True)    # DD/MM/YYYY format
    # Keep old column for backwards compatibility
    formatted_query = Column(Text, nullable=True)
    last_run_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<QueryHistory(id={self.id}, original_query='{self.original_query[:50]}...')>"


class PlatformURL(Base):
    """Model for storing platform and URL information."""

    __tablename__ = "platform_urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    platform = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 0 = inactive, 1 = active
    deleted_at = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<PlatformURL(id={self.id}, platform='{self.platform}', status={self.status})>"
