"""GraphQL connector with query execution, variables, and cursor pagination."""

import time
import requests
from config.settings import get_headers


class GraphQLError(Exception):
    """Custom exception for GraphQL errors."""

    def __init__(self, errors: list, query: str = ""):
        self.errors = errors
        self.query = query
        messages = "; ".join(e.get("message", str(e)) for e in errors)
        super().__init__(f"GraphQL error: {messages}")


def execute_query(
    endpoint_url: str,
    query: str,
    variables: dict | None = None,
    retries: int = 3,
    timeout: int = 60,
) -> dict:
    """Execute a GraphQL query.

    Args:
        endpoint_url: Full GraphQL endpoint URL.
        query: GraphQL query string.
        variables: Query variables dict.
        retries: Number of retry attempts.
        timeout: Request timeout in seconds.

    Returns:
        The "data" field from the GraphQL response.

    Raises:
        GraphQLError: If the response contains errors.
    """
    headers = get_headers()
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    for attempt in range(retries):
        try:
            response = requests.post(
                endpoint_url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )

            if response.status_code >= 400:
                raise GraphQLError(
                    errors=[{"message": f"HTTP {response.status_code}: {response.text[:500]}"}],
                    query=query,
                )

            result = response.json()

            if "errors" in result and result["errors"]:
                raise GraphQLError(errors=result["errors"], query=query)

            return result.get("data", {})

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                raise GraphQLError(
                    errors=[{"message": "Request failed after all retries"}],
                    query=query,
                )


def fetch_all_pages_relay(
    endpoint_url: str,
    query: str,
    variables: dict | None = None,
    connection_path: str = "",
    max_pages: int = 100,
    page_size: int = 50,
    rate_limit_delay: float = 0.2,
) -> list[dict]:
    """Fetch all pages using Relay-style cursor pagination.

    Expects the query to have an `$after` variable and the response to follow
    the Relay connection pattern: { edges { node { ... } }, pageInfo { hasNextPage, endCursor } }

    Args:
        endpoint_url: Full GraphQL endpoint URL.
        query: GraphQL query with $after and $first variables.
        variables: Base variables (will add $after and $first).
        connection_path: Dot-separated path to the connection field in the response
                         (e.g., "user.posts" for data.user.posts).
        max_pages: Maximum number of pages to fetch.
        page_size: Number of items per page.
        rate_limit_delay: Seconds between requests.

    Returns:
        List of node dicts from all pages.
    """
    all_nodes = []
    variables = dict(variables or {})
    variables["first"] = page_size
    cursor = None

    for _ in range(max_pages):
        if cursor:
            variables["after"] = cursor
        elif "after" in variables:
            del variables["after"]

        data = execute_query(endpoint_url, query, variables=variables)

        connection = _resolve_path(data, connection_path) if connection_path else data
        if not connection:
            break

        edges = connection.get("edges", [])
        for edge in edges:
            node = edge.get("node", edge)
            all_nodes.append(node)

        page_info = connection.get("pageInfo", {})
        if not page_info.get("hasNextPage", False):
            break

        cursor = page_info.get("endCursor")
        if not cursor:
            break

        time.sleep(rate_limit_delay)

    return all_nodes


def _resolve_path(data: dict, path: str) -> dict | None:
    """Resolve a dot-separated path in a nested dict.

    Args:
        data: The dict to traverse.
        path: Dot-separated path (e.g., "user.posts").

    Returns:
        The value at the path, or None if not found.
    """
    if not path:
        return data

    current = data
    for key in path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current
