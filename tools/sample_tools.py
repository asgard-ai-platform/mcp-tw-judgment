"""Sample tools demonstrating the @mcp.tool() pattern with different connector types.

TODO: Replace these sample tools with your actual service tools.
      Each tool should use the appropriate connector from connectors/.
"""

from typing import Optional

from pydantic import Field

from app import mcp
from connectors.rest_client import api_get, fetch_all_pages


# =============================================================================
# Example 1: Simple single-resource GET
# =============================================================================

@mcp.tool()
def get_item(
    item_id: str = Field(description="The unique ID of the item to retrieve"),
) -> dict:
    """Get details of a specific item by ID."""
    data = api_get("get_item", path_params={"item_id": item_id})
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "status": data.get("status"),
        "created_at": data.get("created_at"),
    }


# =============================================================================
# Example 2: Paginated list query with filters
# =============================================================================

@mcp.tool()
def list_items(
    status: Optional[str] = Field(default=None, description="Filter by status (e.g., active, archived)"),
    limit: int = Field(default=50, description="Maximum number of items to return"),
) -> dict:
    """List all items with optional filtering."""
    params = {}
    if status:
        params["status"] = status

    items = fetch_all_pages(
        "list_items",
        params=params,
        max_pages=max(1, limit // 50),
    )

    return {
        "total": len(items),
        "items": items[:limit],
    }


# =============================================================================
# Example 3: Aggregation / analytics tool
# =============================================================================

@mcp.tool()
def get_item_summary(
    days: int = Field(default=30, description="Number of days to analyze"),
) -> dict:
    """Get a summary of items created in the last N days."""
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    items = fetch_all_pages(
        "list_items",
        params={
            "created_after": start_date.strftime("%Y-%m-%d"),
            "created_before": end_date.strftime("%Y-%m-%d"),
        },
    )

    status_counts = {}
    for item in items:
        s = item.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "period_days": days,
        "total_items": len(items),
        "by_status": status_counts,
    }
