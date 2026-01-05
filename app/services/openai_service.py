"""OpenAI service for query formatting."""

import json
import logging
from typing import Optional
from datetime import datetime, timedelta
from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.core.config import Settings
from app.core.exceptions import OpenAIServiceError, RateLimitExceededError

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""

    SYSTEM_PROMPT = """
You are a job search query formatter.

Your task is to convert a natural language job search query into a structured JSON output with an optimized Google search query.

CRITICAL RULES (MANDATORY):
- You MUST ALWAYS return ALL applicable title variations from the predefined list below.
- You are NOT allowed to omit any matching variation.
- You are NOT allowed to invent new titles outside the list.
- The number of variations MUST be consistent across requests for the same input.
- Ordering MUST be exactly as listed.
- If a rule is violated, the output is invalid.

--------------------------------------------------
JOB TITLE VARIATION DICTIONARY (EXHAUSTIVE)

If the role is Senior Software Engineer / Senior Developer, you MUST include ALL of the following:

[
  "senior software engineer",
  "senior software developer",
  "senior developer",
  "senior sde",
  "senior backend engineer",
  "senior backend developer",
  "senior full stack engineer",
  "senior full-stack engineer"
  "Software Engineer"
  "Senior Frontend developer"
  "frontend developer"
]

--------------------------------------------------

QUERY FORMATTING RULES:
1. Group job titles using parentheses and OR
2. Use quotes for exact phrases
3. Extract locations
4. Extract skills and include common variations as OR groups
5. Parse time filters and convert them to date ranges
6. Use uppercase OR only
7. Parentheses are mandatory for grouped terms

--------------------------------------------------

RETURN FORMAT (STRICT — NO EXTRA TEXT):

{
  "query_string": "string",
  "locations": ["array"],
  "duration": {
    "from": "DD/MM/YYYY",
    "to": "DD/MM/YYYY"
  }
}

DEFAULTS:
- If no time filter is specified, use last 7 days
- Current date is: {{CURRENT_DATE}}
"""

    def __init__(self, settings: Settings):
        """
        Initialize OpenAI service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout
        )
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APITimeoutError, OpenAIError)),
        reraise=True
    )
    async def format_query(self, query: str) -> tuple[dict, dict]:
        """
        Format a natural language query into a structured search query with metadata.

        Args:
            query: Natural language job search query

        Returns:
            Tuple of (formatted_query_data, metadata)
            formatted_query_data contains:
                - query_string: Optimized Google search query
                - locations: List of extracted locations
                - duration: Dict with 'from' and 'to' dates

        Raises:
            OpenAIServiceError: If OpenAI API call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        try:
            logger.info(f"Formatting query: {query[:100]}...")

            # Replace current date placeholder in the prompt
            current_date = datetime.now().strftime("%d/%m/%Y")
            system_prompt = self.SYSTEM_PROMPT.replace("{{CURRENT_DATE}}", current_date)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Format this job search query: {query}"}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content.strip()

            try:
                formatted_query_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response_content}")
                raise OpenAIServiceError(f"Invalid JSON response from OpenAI: {str(e)}")

            metadata = {
                "model": self.model,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "finish_reason": response.choices[0].finish_reason
            }

            logger.info(
                f"Query formatted successfully. Tokens used: {metadata['tokens_used']}"
            )

            return formatted_query_data, metadata

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            raise RateLimitExceededError(
                "OpenAI rate limit exceeded. Please try again later."
            )

        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {str(e)}")
            raise OpenAIServiceError(
                "Request to OpenAI timed out. Please try again."
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise OpenAIServiceError(
                f"Failed to format query: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in format_query: {str(e)}", exc_info=True)
            raise OpenAIServiceError(
                "An unexpected error occurred while formatting the query"
            )


def get_openai_service(settings: Settings) -> OpenAIService:
    """
    Factory function to create OpenAI service instance.

    Args:
        settings: Application settings

    Returns:
        OpenAIService instance
    """
    return OpenAIService(settings)
