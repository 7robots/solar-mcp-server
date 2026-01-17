"""
Example MCP Server Template for FastMCP Cloud.

This template demonstrates best practices for building MCP servers with FastMCP 2
for deployment to fastmcp.cloud. Replace the example tools with your own implementation.

Usage:
    Local:  python server.py
    Test:   fastmcp inspect server.py
    Deploy: Push to GitHub, connect to fastmcp.cloud
"""

import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# Configuration
# =============================================================================

# Load from environment variables (set in .env locally, fastmcp.cloud in production)
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.example.com/v1")
API_TOKEN = os.environ.get("API_TOKEN", "")

# Initialize MCP server
mcp = FastMCP(
    "example-mcp",
    instructions="""
    Example MCP server demonstrating FastMCP 2 patterns.

    Available tools:
    - example_list_items: List items with filtering and pagination
    - example_get_item: Get a specific item by ID
    - example_search_items: Search items by name
    - example_create_item: Create a new item
    - example_get_stats: Get collection statistics

    All tools support 'response_format' parameter:
    - 'json' (default): Structured data for programmatic use
    - 'markdown': Human-readable formatted output
    """,
)


# =============================================================================
# Enums and Models
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class ItemType(str, Enum):
    """Valid item types."""

    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    OTHER = "other"


# =============================================================================
# Utility Functions
# =============================================================================


async def make_api_request(
    endpoint: str,
    method: str = "GET",
    params: Dict[str, Any] = None,
    json_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Make authenticated API request.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        params: Query parameters
        json_data: JSON body data

    Returns:
        Parsed JSON response

    Raises:
        httpx.HTTPStatusError: On HTTP errors
    """
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE_URL}/{endpoint}",
            headers=headers,
            params=params,
            json=json_data,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


def handle_api_error(e: Exception) -> str:
    """Format API errors consistently.

    Args:
        e: Exception to format

    Returns:
        User-friendly error message
    """
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return "Error: Authentication failed. Check API_TOKEN configuration."
        elif status == 403:
            return "Error: Permission denied. Insufficient access rights."
        elif status == 404:
            return "Error: Resource not found. Verify the ID is correct."
        elif status == 429:
            return "Error: Rate limit exceeded. Please wait before retrying."
        elif status >= 500:
            return f"Error: Server error ({status}). Try again later."
        return f"Error: API request failed with status {status}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, httpx.ConnectError):
        return "Error: Could not connect to API. Check network and API_BASE_URL."
    return f"Error: {type(e).__name__}: {e}"


def format_item_markdown(item: Dict[str, Any]) -> str:
    """Format a single item as markdown.

    Args:
        item: Item dictionary

    Returns:
        Markdown formatted string
    """
    lines = [f"## {item.get('name', 'Unnamed')} (ID: {item.get('id', 'N/A')})"]
    lines.append(f"**Type**: {item.get('type', 'unknown')}")

    if item.get("description"):
        lines.append(f"**Description**: {item['description']}")

    if item.get("created_at"):
        lines.append(f"**Created**: {item['created_at']}")

    if item.get("tags"):
        lines.append(f"**Tags**: {', '.join(item['tags'])}")

    return "\n".join(lines)


# =============================================================================
# Example Data (Replace with real API calls)
# =============================================================================

# Sample data for demonstration - replace with actual API calls
SAMPLE_ITEMS = [
    {
        "id": "item-001",
        "name": "Project Proposal",
        "type": "document",
        "description": "Q1 project proposal document",
        "created_at": "2024-01-15",
        "tags": ["important", "q1"],
    },
    {
        "id": "item-002",
        "name": "Team Photo",
        "type": "image",
        "description": "Annual team photo 2024",
        "created_at": "2024-02-01",
        "tags": ["team", "photo"],
    },
    {
        "id": "item-003",
        "name": "Product Demo",
        "type": "video",
        "description": "Product demonstration video",
        "created_at": "2024-03-10",
        "tags": ["demo", "product"],
    },
]


async def fetch_items(
    limit: int = 20,
    offset: int = 0,
    item_type: str = None,
) -> tuple[List[Dict], int]:
    """Fetch items from data source.

    Replace this with actual API calls in your implementation.
    """
    items = SAMPLE_ITEMS.copy()

    if item_type:
        items = [i for i in items if i["type"] == item_type]

    total = len(items)
    items = items[offset : offset + limit]

    return items, total


async def fetch_item(item_id: str) -> Optional[Dict]:
    """Fetch a single item by ID."""
    for item in SAMPLE_ITEMS:
        if item["id"] == item_id:
            return item
    return None


async def search_items(query: str, limit: int = 20) -> List[Dict]:
    """Search items by name."""
    query_lower = query.lower()
    return [
        item
        for item in SAMPLE_ITEMS
        if query_lower in item["name"].lower() or query_lower in item.get("description", "").lower()
    ][:limit]


# =============================================================================
# MCP Tools
# =============================================================================


@mcp.tool()
async def example_list_items(
    limit: int = 20,
    offset: int = 0,
    item_type: Optional[str] = None,
    response_format: str = "json",
) -> str:
    """List items with optional filtering and pagination.

    Args:
        limit: Maximum items to return (1-100, default 20)
        offset: Items to skip for pagination (default 0)
        item_type: Filter by type ('document', 'image', 'video', 'other')
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        items, total = await fetch_items(limit=limit, offset=offset, item_type=item_type)

        if response_format == "markdown":
            if not items:
                return "No items found matching the criteria."

            lines = ["# Items", ""]
            lines.append(f"Showing {len(items)} of {total} items (offset: {offset})")
            lines.append("")

            for item in items:
                lines.append(format_item_markdown(item))
                lines.append("")

            if total > offset + len(items):
                next_offset = offset + len(items)
                lines.append(f"*{total - next_offset} more items available. Use offset={next_offset} for next page.*")

            return "\n".join(lines)

        return json.dumps(
            {
                "total": total,
                "count": len(items),
                "offset": offset,
                "has_more": total > offset + len(items),
                "next_offset": offset + len(items) if total > offset + len(items) else None,
                "items": items,
            },
            indent=2,
        )

    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def example_get_item(
    item_id: str,
    response_format: str = "json",
) -> str:
    """Get a specific item by ID.

    Args:
        item_id: The unique identifier of the item
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        item = await fetch_item(item_id)

        if not item:
            return f"Error: Item not found with ID '{item_id}'. Use example_list_items to see available items."

        if response_format == "markdown":
            return format_item_markdown(item)

        return json.dumps(item, indent=2)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def example_search_items(
    query: str,
    limit: int = 20,
    response_format: str = "json",
) -> str:
    """Search for items by name or description.

    Args:
        query: Search string (case-insensitive, matches name and description)
        limit: Maximum results (1-100, default 20)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        if not query or not query.strip():
            return "Error: Search query cannot be empty."

        limit = max(1, min(100, limit))
        items = await search_items(query.strip(), limit)

        if not items:
            return f"No items found matching '{query}'."

        if response_format == "markdown":
            lines = [f"# Search Results: '{query}'", ""]
            lines.append(f"Found {len(items)} item(s)")
            lines.append("")

            for item in items:
                lines.append(format_item_markdown(item))
                lines.append("")

            return "\n".join(lines)

        return json.dumps(
            {
                "query": query,
                "count": len(items),
                "items": items,
            },
            indent=2,
        )

    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def example_create_item(
    name: str,
    item_type: str = "document",
    description: Optional[str] = None,
    tags: Optional[str] = None,
) -> str:
    """Create a new item.

    Args:
        name: Item name (required)
        item_type: Type of item ('document', 'image', 'video', 'other')
        description: Optional description
        tags: Optional comma-separated tags (e.g., 'important,urgent')
    """
    try:
        if not name or not name.strip():
            return "Error: Item name cannot be empty."

        # Validate item_type
        valid_types = ["document", "image", "video", "other"]
        if item_type not in valid_types:
            return f"Error: Invalid item_type '{item_type}'. Must be one of: {', '.join(valid_types)}"

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # In a real implementation, this would call the API
        new_item = {
            "id": f"item-{len(SAMPLE_ITEMS) + 1:03d}",
            "name": name.strip(),
            "type": item_type,
            "description": description.strip() if description else None,
            "tags": tag_list,
            "created_at": "2024-01-01",  # Would be actual timestamp
        }

        return json.dumps(
            {
                "success": True,
                "message": f"Item '{name}' created successfully",
                "item": new_item,
            },
            indent=2,
        )

    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def example_get_stats(
    response_format: str = "json",
) -> str:
    """Get statistics about the item collection.

    Args:
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        items = SAMPLE_ITEMS

        # Calculate statistics
        total = len(items)
        type_counts = {}
        for item in items:
            item_type = item.get("type", "unknown")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        stats = {
            "total_items": total,
            "type_distribution": type_counts,
        }

        if response_format == "markdown":
            lines = ["# Collection Statistics", ""]
            lines.append(f"**Total Items**: {total}")
            lines.append("")
            lines.append("## Items by Type")
            for item_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                lines.append(f"- {item_type}: {count}")

            return "\n".join(lines)

        return json.dumps(stats, indent=2)

    except Exception as e:
        return handle_api_error(e)


# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    # HTTP transport for fastmcp.cloud deployment
    # MCP_HOST and MCP_PORT are automatically set by fastmcp.cloud
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
