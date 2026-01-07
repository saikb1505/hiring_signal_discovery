"""Database models using SQLAlchemy ORM."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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


class SearchResult(Base):
    """Model for storing search results."""

    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_history_id = Column(Integer, ForeignKey("query_history.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platform_urls.id"), nullable=True, index=True)
    search_id = Column(String(255), nullable=True, index=True)  # External search ID from search API

    # Result details
    position = Column(Integer, nullable=True)
    title = Column(Text, nullable=False)
    link = Column(String(2048), nullable=False)
    snippet = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)

    # Additional metadata from search API
    redirect_link = Column(String(2048), nullable=True)
    displayed_link = Column(String(2048), nullable=True)
    favicon = Column(String(2048), nullable=True)
    snippet_highlighted_words = Column(JSON, nullable=True, default=list)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    query_history = relationship("QueryHistory", backref="search_results")
    platform = relationship("PlatformURL", backref="search_results")

    def __repr__(self):
        return f"<SearchResult(id={self.id}, query_history_id={self.query_history_id}, title='{self.title[:50]}...')>"
