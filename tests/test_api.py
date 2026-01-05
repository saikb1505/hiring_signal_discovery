"""Tests for API endpoints."""

import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


class TestFormatQueryEndpoint:
    """Tests for /format-query endpoint."""

    def test_format_query_success(self, client, mock_openai_response):
        """Test successful query formatting."""
        with patch('app.services.openai_service.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = mock_openai_response

            response = client.post(
                "/format-query",
                json={"query": "Software engineer in Hyderabad"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "original_query" in data
            assert "query_string" in data
            assert "locations" in data
            assert "duration" in data
            assert data["original_query"] == "Software engineer in Hyderabad"
            assert isinstance(data["locations"], list)
            assert "from" in data["duration"]
            assert "to" in data["duration"]

    def test_format_query_empty_string(self, client):
        """Test with empty query string."""
        response = client.post(
            "/format-query",
            json={"query": ""}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_format_query_whitespace_only(self, client):
        """Test with whitespace-only query."""
        response = client.post(
            "/format-query",
            json={"query": "   "}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_format_query_missing_field(self, client):
        """Test with missing query field."""
        response = client.post("/format-query", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
