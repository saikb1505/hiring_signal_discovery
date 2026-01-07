"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class SearchQueryRequest(BaseModel):
    """Request schema for search query formatting."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language job search query",
        examples=["Senior software engineer in Hyderabad with Ruby on Rails and MySQL"]
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query string."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or contain only whitespace")
        return v.strip()


class DurationSchema(BaseModel):
    """Schema for duration/date range."""

    from_date: str = Field(
        ...,
        alias="from",
        description="Start date in DD/MM/YYYY format"
    )
    to_date: str = Field(
        ...,
        alias="to",
        description="End date in DD/MM/YYYY format"
    )

    class Config:
        populate_by_name = True


class FormattedQueryResponse(BaseModel):
    """Response schema for formatted query."""

    original_query: str = Field(
        ...,
        description="The original search query provided by the user"
    )
    query_string: str = Field(
        ...,
        description="The formatted Google search query string"
    )
    locations: List[str] = Field(
        default_factory=list,
        description="List of extracted locations"
    )
    duration: DurationSchema = Field(
        ...,
        description="Date range for the search"
    )
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata about the formatting process"
    )


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Deployment environment")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


class PlatformURLCreate(BaseModel):
    """Request schema for creating a platform URL."""

    platform: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Platform name",
        examples=["LinkedIn"]
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Platform URL",
        examples=["https://www.linkedin.com/jobs/search"]
    )
    status: int = Field(
        default=1,
        ge=0,
        le=1,
        description="Status: 0 = inactive, 1 = active"
    )

    @field_validator("platform", "url")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or contain only whitespace")
        return v.strip()


class PlatformURLUpdate(BaseModel):
    """Request schema for updating a platform URL."""

    platform: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Platform name"
    )
    url: Optional[str] = Field(
        None,
        min_length=1,
        max_length=2048,
        description="Platform URL"
    )
    status: Optional[int] = Field(
        None,
        ge=0,
        le=1,
        description="Status: 0 = inactive, 1 = active"
    )

    @field_validator("platform", "url")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate string fields are not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field cannot be empty or contain only whitespace")
        return v.strip() if v else None


class PlatformURLResponse(BaseModel):
    """Response schema for platform URL."""

    id: int = Field(..., description="Platform URL ID")
    platform: str = Field(..., description="Platform name")
    url: str = Field(..., description="Platform URL")
    status: int = Field(..., description="Status: 0 = inactive, 1 = active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    """Response schema for query history."""

    id: int = Field(..., description="Query history ID")
    original_query: str = Field(..., description="Original user query")
    query_string: str = Field(..., description="Formatted search query string")
    locations: List[str] = Field(default_factory=list, description="Extracted locations")
    duration_from: Optional[str] = Field(None, description="Start date in DD/MM/YYYY format")
    duration_to: Optional[str] = Field(None, description="End date in DD/MM/YYYY format")
    formatted_query: Optional[str] = Field(None, description="Complete formatted query for platform")
    last_run_at: str = Field(..., description="Last run timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class QueryHistoryUpdate(BaseModel):
    """Request schema for updating a query history."""

    original_query: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Original user query"
    )
    query_string: Optional[str] = Field(
        None,
        min_length=1,
        description="Formatted search query string"
    )
    locations: Optional[List[str]] = Field(
        None,
        description="Extracted locations"
    )
    duration_from: Optional[str] = Field(
        None,
        description="Start date in DD/MM/YYYY format"
    )
    duration_to: Optional[str] = Field(
        None,
        description="End date in DD/MM/YYYY format"
    )

    @field_validator("original_query", "query_string")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate string fields are not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field cannot be empty or contain only whitespace")
        return v.strip() if v else None


class SearchResultCreate(BaseModel):
    """Request schema for creating a search result."""

    query_history_id: int = Field(..., description="Query history ID")
    platform_id: Optional[int] = Field(None, description="Platform ID")
    search_id: Optional[str] = Field(None, description="External search ID")
    position: Optional[int] = Field(None, description="Position in search results")
    title: str = Field(..., min_length=1, description="Result title")
    link: str = Field(..., min_length=1, description="Result URL")
    snippet: Optional[str] = Field(None, description="Result snippet")
    source: Optional[str] = Field(None, description="Result source")
    redirect_link: Optional[str] = Field(None, description="Redirect URL")
    displayed_link: Optional[str] = Field(None, description="Displayed URL")
    favicon: Optional[str] = Field(None, description="Favicon URL")
    snippet_highlighted_words: Optional[List[str]] = Field(
        default_factory=list,
        description="Highlighted words in snippet"
    )


class SearchResultResponse(BaseModel):
    """Response schema for search result."""

    id: int = Field(..., description="Search result ID")
    query_history_id: int = Field(..., description="Query history ID")
    platform_id: Optional[int] = Field(None, description="Platform ID")
    search_id: Optional[str] = Field(None, description="External search ID")
    position: Optional[int] = Field(None, description="Position in search results")
    title: str = Field(..., description="Result title")
    link: str = Field(..., description="Result URL")
    snippet: Optional[str] = Field(None, description="Result snippet")
    source: Optional[str] = Field(None, description="Result source")
    redirect_link: Optional[str] = Field(None, description="Redirect URL")
    displayed_link: Optional[str] = Field(None, description="Displayed URL")
    favicon: Optional[str] = Field(None, description="Favicon URL")
    snippet_highlighted_words: Optional[List[str]] = Field(
        default_factory=list,
        description="Highlighted words in snippet"
    )
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
