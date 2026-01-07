"""SerpAPI service for web search."""

import logging
from typing import Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.core.config import Settings
from app.core.exceptions import SerpAPIServiceError, RateLimitExceededError

logger = logging.getLogger(__name__)


class SerpAPIService:
    """Service for interacting with SerpAPI."""

    SERPAPI_URL = "https://serpapi.com/search"

    def __init__(self, settings: Settings):
        """
        Initialize SerpAPI service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_key = settings.serpapi_api_key
        self.timeout = settings.serpapi_timeout
        self.max_results = settings.serpapi_max_results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
        reraise=True
    )
    async def search(self, formatted_query: str, num_results: Optional[int] = None) -> dict:
        """
        Perform a Google search using SerpAPI.

        Args:
            formatted_query: The formatted search query
            num_results: Number of results to return (defaults to settings value)

        Returns:
            Dictionary containing search results and metadata

        Raises:
            SerpAPIServiceError: If SerpAPI call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        try:
            logger.info(f"Searching with SerpAPI query: {formatted_query[:100]}...")

            params = {
                "q": formatted_query,
                "api_key": self.api_key,
                "engine": "google",
                "num": num_results or self.max_results,
                "output": "json"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.SERPAPI_URL,
                    params=params
                )
                

                # Handle rate limiting
                if response.status_code == 429:
                    logger.error("SerpAPI rate limit exceeded")
                    raise RateLimitExceededError(
                        "SerpAPI rate limit exceeded. Please try again later."
                    )

                # Handle other HTTP errors
                response.raise_for_status()

                data = response.json()

                # Check for SerpAPI-specific errors
                if "error" in data:
                    error_msg = data.get("error", "Unknown error")
                    logger.error(f"SerpAPI error: {error_msg}")
                    raise SerpAPIServiceError(f"SerpAPI error: {error_msg}")

                # Extract organic results
                organic_results = data.get("organic_results", [])

                result = {
                    "query": formatted_query,
                    "results": organic_results,
                    "total_results": len(organic_results),
                    "search_metadata": {
                        "total_results": data.get("search_information", {}).get("total_results"),
                        "time_taken": data.get("search_information", {}).get("time_taken_displayed"),
                        "search_id": data.get("search_metadata", {}).get("id")
                    },
                    "knowledge_graph": data.get("knowledge_graph"),
                    "answer_box": data.get("answer_box")
                }

                logger.info(
                    f"SerpAPI search completed successfully. Found {len(organic_results)} results"
                )

                return result

        except httpx.TimeoutException as e:
            logger.error(f"SerpAPI timeout: {str(e)}")
            raise SerpAPIServiceError(
                "Request to SerpAPI timed out. Please try again."
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("SerpAPI rate limit exceeded")
                raise RateLimitExceededError(
                    "SerpAPI rate limit exceeded. Please try again later."
                )
            logger.error(f"SerpAPI HTTP error: {str(e)}")
            raise SerpAPIServiceError(
                f"SerpAPI request failed with status {e.response.status_code}"
            )

        except httpx.HTTPError as e:
            logger.error(f"SerpAPI HTTP error: {str(e)}")
            raise SerpAPIServiceError(
                f"Failed to perform search: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in SerpAPI search: {str(e)}", exc_info=True)
            raise SerpAPIServiceError(
                "An unexpected error occurred while performing the search"
            )


def get_serpapi_service(settings: Settings) -> SerpAPIService:
    """
    Factory function to create SerpAPI service instance.

    Args:
        settings: Application settings

    Returns:
        SerpAPIService instance
    """
    return SerpAPIService(settings)
