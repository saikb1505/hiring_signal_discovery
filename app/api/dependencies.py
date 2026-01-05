"""FastAPI dependencies for dependency injection."""

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.openai_service import OpenAIService, get_openai_service


def get_cached_openai_service(
    settings: Settings = Depends(get_settings)
) -> OpenAIService:
    """
    Get cached OpenAI service instance.

    Args:
        settings: Application settings

    Returns:
        Cached OpenAIService instance
    """
    return get_openai_service(settings)
