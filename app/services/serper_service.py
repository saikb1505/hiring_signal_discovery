"""SerperAPI service for web search."""

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
from app.core.exceptions import SerperServiceError, RateLimitExceededError

logger = logging.getLogger(__name__)


class SerperService:
    """Service for interacting with SerperAPI."""

    SERPER_API_URL = "https://google.serper.dev/search"

    def __init__(self, settings: Settings):
        """
        Initialize Serper service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_key = settings.serper_api_key
        self.timeout = settings.serper_timeout
        self.max_results = settings.serper_max_results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
        reraise=True
    )
    async def search(self, formatted_query: str, num_results: Optional[int] = None) -> dict:
        """
        Perform a Google search using SerperAPI.

        Args:
            formatted_query: The formatted search query
            num_results: Number of results to return (defaults to settings value)

        Returns:
            Dictionary containing search results and metadata

        Raises:
            SerperServiceError: If SerperAPI call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        try:
            logger.info(f"Searching with query: {formatted_query[:100]}...")

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": formatted_query,
                "num": num_results or self.max_results
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.SERPER_API_URL,
                    headers=headers,
                    json=payload
                )

                # Handle rate limiting
                if response.status_code == 429:
                    logger.error("SerperAPI rate limit exceeded")
                    raise RateLimitExceededError(
                        "SerperAPI rate limit exceeded. Please try again later."
                    )

                # Handle other HTTP errors
                response.raise_for_status()

                data = response.json()

                # Extract organic results
                organic_results = data.get("organic", [])

                result = {
                    "query": formatted_query,
                    "results": organic_results,
                    "total_results": len(organic_results),
                    "search_metadata": {
                        "total_results": data.get("searchInformation", {}).get("totalResults"),
                        "time_taken": data.get("searchInformation", {}).get("formattedSearchTime"),
                    },
                    "knowledge_graph": data.get("knowledgeGraph"),
                    "answer_box": data.get("answerBox")
                }
                
                logger.info(
                    f"Search completed successfully. Found {len(organic_results)} results"
                )

                return result

        except httpx.TimeoutException as e:
            logger.error(f"SerperAPI timeout: {str(e)}")
            raise SerperServiceError(
                "Request to SerperAPI timed out. Please try again."
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("SerperAPI rate limit exceeded")
                raise RateLimitExceededError(
                    "SerperAPI rate limit exceeded. Please try again later."
                )
            logger.error(f"SerperAPI HTTP error: {str(e)}")
            raise SerperServiceError(
                f"SerperAPI request failed with status {e.response.status_code}"
            )

        except httpx.HTTPError as e:
            logger.error(f"SerperAPI HTTP error: {str(e)}")
            raise SerperServiceError(
                f"Failed to perform search: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in search: {str(e)}", exc_info=True)
            raise SerperServiceError(
                "An unexpected error occurred while performing the search"
            )


def get_serper_service(settings: Settings) -> SerperService:
    """
    Factory function to create Serper service instance.

    Args:
        settings: Application settings

    Returns:
        SerperService instance
    """
    return SerperService(settings)
