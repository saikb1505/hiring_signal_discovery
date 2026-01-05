"""Utility functions for building formatted search queries."""

from typing import List, Dict


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
