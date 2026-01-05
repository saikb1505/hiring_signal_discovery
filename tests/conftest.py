"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from main import app
from app.core.config import Settings


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        openai_api_key="test-api-key",
        environment="test",
        debug=True
    )


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Create mock OpenAI response."""
    import json
    response_json = {
        "query_string": '("software engineer" OR "developer" OR "sde") after:2025-12-18 before:2025-12-25',
        "locations": ["Hyderabad"],
        "duration": {
            "from": "18/12/2025",
            "to": "25/12/2025"
        }
    }
    return Mock(
        choices=[
            Mock(
                message=Mock(
                    content=json.dumps(response_json)
                ),
                finish_reason="stop"
            )
        ],
        usage=Mock(
            total_tokens=100,
            prompt_tokens=50,
            completion_tokens=50
        )
    )
