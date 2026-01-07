"""Utility functions for building formatted search queries."""

from typing import List, Dict, Tuple


def build_platform_formatted_queries(
    query_string: str,
    locations: List[str],
    platform_urls: List[Dict[str, str]]
) -> List[str]:
    """
    Build formatted queries for multiple platforms.

    Args:
        query_string: The search query string with job titles
        locations: List of location strings
        platform_urls: List of platform URL dictionaries with 'url' key

    Returns:
        List of formatted queries, one for each platform

    Example:
        Input:
            query_string: '("senior software engineer" OR "senior developer")'
            locations: ['Bangalore', 'Mumbai']
            platform_urls: [{'url': 'greenhouse.io'}, {'url': 'lever.co'}]

        Output:
            [
                'site:greenhouse.io ("senior software engineer" OR "senior developer") (Bangalore OR Mumbai)',
                'site:lever.co ("senior software engineer" OR "senior developer") (Bangalore OR Mumbai)'
            ]
    """
    formatted_queries = []

    # Build location part
    location_part = ""
    if locations:
        if len(locations) == 1:
            location_part = f"({locations[0]})"
        else:
            location_part = f"({' OR '.join(locations)})"

    # Build formatted query for each platform
    for platform in platform_urls:
        url = platform.get('url', '')
        if not url:
            continue

        # Build the complete query
        parts = [f"site:{url}", query_string]
        if location_part:
            parts.append(location_part)

        formatted_query = " ".join(parts)
        formatted_queries.append(formatted_query)

    return formatted_queries


def build_platform_formatted_queries_with_ids(
    query_string: str,
    locations: List[str],
    platform_data: List[Dict]
) -> List[Tuple[str, int, str]]:
    """
    Build formatted queries for multiple platforms with platform IDs and URLs.

    Args:
        query_string: The search query string with job titles
        locations: List of location strings
        platform_data: List of dictionaries with 'id' and 'url' keys

    Returns:
        List of tuples (formatted_query, platform_id, platform_url)

    Example:
        Input:
            query_string: '("senior software engineer" OR "senior developer")'
            locations: ['Bangalore', 'Mumbai']
            platform_data: [{'id': 1, 'url': 'greenhouse.io'}, {'id': 2, 'url': 'lever.co'}]

        Output:
            [
                ('site:greenhouse.io ("senior software engineer" OR "senior developer") (Bangalore OR Mumbai)', 1, 'greenhouse.io'),
                ('site:lever.co ("senior software engineer" OR "senior developer") (Bangalore OR Mumbai)', 2, 'lever.co')
            ]
    """
    formatted_queries = []

    # Build location part
    location_part = ""
    if locations:
        if len(locations) == 1:
            location_part = f"({locations[0]})"
        else:
            location_part = f"({' OR '.join(locations)})"

    # Build formatted query for each platform
    for platform in platform_data:
        url = platform.get('url', '')
        platform_id = platform.get('id')
        if not url or platform_id is None:
            continue

        # Build the complete query
        parts = [f"site:{url}", query_string]
        if location_part:
            parts.append(location_part)

        formatted_query = " ".join(parts)
        formatted_queries.append((formatted_query, platform_id, url))

    return formatted_queries
