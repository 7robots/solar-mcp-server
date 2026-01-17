# FastMCP 2 Patterns Guide

## Server Initialization

```python
from fastmcp import FastMCP

mcp = FastMCP(
    "service-name-mcp",
    instructions="Clear description of server capabilities for LLM discovery.",
)
```

**Server naming**: Use `{service}-mcp` or `{service}-{qualifier}-mcp` format.

---

## Tool Registration

### Basic Tool

```python
@mcp.tool()
async def service_get_item(item_id: str) -> str:
    """Get an item by ID.

    Args:
        item_id: The unique identifier of the item

    Returns:
        JSON string with item details
    """
    item = await fetch_item(item_id)
    return json.dumps(item, indent=2)
```

### Tool with Pydantic Validation

```python
from pydantic import BaseModel, Field, ConfigDict

class ListItemsInput(BaseModel):
    """Input model for listing items."""

    model_config = ConfigDict(str_strip_whitespace=True)

    limit: int = Field(
        default=20,
        description="Maximum items to return",
        ge=1,
        le=100,
    )
    offset: int = Field(
        default=0,
        description="Items to skip for pagination",
        ge=0,
    )
    filter_type: Optional[str] = Field(
        default=None,
        description="Filter by type (e.g., 'active', 'archived')",
    )

@mcp.tool()
async def service_list_items(
    limit: int = 20,
    offset: int = 0,
    filter_type: Optional[str] = None,
) -> str:
    """List items with optional filtering and pagination."""
    # Implementation
    pass
```

### Tool with Field Validators

```python
from pydantic import field_validator

class GetItemInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    item_id: str = Field(..., description="Item ID (UUID format)")

    @field_validator("item_id")
    @classmethod
    def validate_item_id(cls, v: str) -> str:
        if len(v) != 36 or v.count("-") != 4:
            raise ValueError("Invalid UUID format")
        return v
```

---

## Response Formats

### Supporting Multiple Formats

```python
from enum import Enum

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

@mcp.tool()
async def service_list_items(
    limit: int = 20,
    response_format: str = "json",
) -> str:
    """List items.

    Args:
        limit: Maximum items to return (1-100)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    items = await fetch_items(limit)

    if response_format == "markdown":
        return format_items_markdown(items)

    return json.dumps({
        "count": len(items),
        "items": items
    }, indent=2)
```

### Markdown Formatting Helper

```python
def format_item_markdown(item: dict) -> str:
    """Format a single item as markdown."""
    lines = [
        f"## {item['name']} (ID: {item['id']})",
        f"**Type**: {item['type']}",
        f"**Status**: {item['status']}",
    ]
    if item.get("description"):
        lines.append(f"**Description**: {item['description']}")
    return "\n".join(lines)

def format_items_list_markdown(items: list, title: str = "Items") -> str:
    """Format a list of items as markdown."""
    lines = [f"# {title}", "", f"Found {len(items)} item(s)", ""]
    for item in items:
        lines.append(format_item_markdown(item))
        lines.append("")
    return "\n".join(lines)
```

---

## Pagination Pattern

```python
@mcp.tool()
async def service_list_items(
    limit: int = 20,
    offset: int = 0,
    response_format: str = "json",
) -> str:
    """List items with pagination.

    Args:
        limit: Max items to return (1-100, default 20)
        offset: Items to skip for pagination (default 0)
        response_format: 'json' or 'markdown'
    """
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    total = await get_total_count()
    items = await fetch_items(limit=limit, offset=offset)

    if response_format == "markdown":
        lines = ["# Items", ""]
        lines.append(f"Showing {len(items)} of {total} (offset: {offset})")
        lines.append("")
        for item in items:
            lines.append(format_item_markdown(item))
            lines.append("")
        if total > offset + len(items):
            next_offset = offset + len(items)
            lines.append(f"*Use offset={next_offset} for next page*")
        return "\n".join(lines)

    return json.dumps({
        "total": total,
        "count": len(items),
        "offset": offset,
        "has_more": total > offset + len(items),
        "next_offset": offset + len(items) if total > offset + len(items) else None,
        "items": items,
    }, indent=2)
```

---

## HTTP Client Pattern

### Shared API Client

```python
import httpx

API_BASE_URL = "https://api.example.com/v1"
API_TOKEN = os.environ.get("API_TOKEN", "")

async def make_api_request(
    endpoint: str,
    method: str = "GET",
    params: dict = None,
    json_data: dict = None,
) -> dict:
    """Make authenticated API request."""
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
```

### Error Handling

```python
def handle_api_error(e: Exception) -> str:
    """Format API errors consistently."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return "Error: Authentication failed. Check API credentials."
        elif status == 403:
            return "Error: Permission denied."
        elif status == 404:
            return "Error: Resource not found."
        elif status == 429:
            return "Error: Rate limit exceeded. Wait before retrying."
        return f"Error: API request failed with status {status}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    return f"Error: {type(e).__name__}: {e}"
```

---

## Complete Tool Example

```python
@mcp.tool()
async def service_search_items(
    query: str,
    limit: int = 20,
    response_format: str = "json",
) -> str:
    """Search for items by name or description.

    Args:
        query: Search string (case-insensitive)
        limit: Maximum results (1-100, default 20)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        limit = max(1, min(100, limit))

        items = await make_api_request(
            "items/search",
            params={"q": query, "limit": limit}
        )

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

        return json.dumps({
            "query": query,
            "count": len(items),
            "items": items
        }, indent=2)

    except Exception as e:
        return handle_api_error(e)
```

---

## Server Entry Point

```python
if __name__ == "__main__":
    # HTTP transport for fastmcp.cloud deployment
    # MCP_HOST and MCP_PORT are set by fastmcp.cloud
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
```

---

## Quality Checklist

Before deploying, verify:

- [ ] All tools have descriptive names with service prefix
- [ ] All tools have clear docstrings
- [ ] Input validation using type hints or Pydantic
- [ ] Support for JSON and Markdown response formats
- [ ] Pagination for list operations
- [ ] Consistent error handling
- [ ] Async/await for all I/O operations
- [ ] Environment variables for secrets (never hardcoded)
- [ ] `.gitignore` excludes `.env` and `__pycache__`
- [ ] Server tested locally before deployment
