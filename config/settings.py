import os

# =============================================================================
# TODO: Update these values for your service
# =============================================================================

# API base URL
BASE_URL = "https://api.example.com"

# API version prefix
API_VERSION = "v1"

# Default pagination size
DEFAULT_PER_PAGE = 50

# =============================================================================
# Auth — choose ONE auth module and import it here
# =============================================================================
# For Bearer token auth:
# from auth.bearer import get_auth_headers
#
# For API key auth:
# from auth.api_key import get_auth_headers
#
# For OAuth 2.0 auth:
# from auth.oauth2 import get_auth_headers
#
# For no auth (public APIs):
# from auth.none import get_auth_headers

from auth.bearer import get_auth_headers  # TODO: change to your auth module

# =============================================================================
# Endpoint map — define your API endpoints here
# =============================================================================
# Supports path parameter substitution: {param} will be replaced by kwargs
#
# Example:
#   ENDPOINTS = {
#       "orders": "/v1/orders",
#       "order_detail": "/v1/orders/{order_id}",
#       "products": "/v1/products",
#       "product_detail": "/v1/products/{product_id}",
#   }

ENDPOINTS = {
    "list_items": f"/{API_VERSION}/items",
    "get_item": f"/{API_VERSION}/items/{{item_id}}",
}


def get_headers() -> dict:
    """Get request headers including auth."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    headers.update(get_auth_headers())
    return headers


def get_url(endpoint_key: str, **kwargs) -> str:
    """Build full URL for an endpoint with path parameter substitution.

    Args:
        endpoint_key: Key from ENDPOINTS dict.
        **kwargs: Path parameters to substitute (e.g., item_id="123").

    Returns:
        Full URL string.

    Raises:
        KeyError: If endpoint_key not found in ENDPOINTS.
    """
    path = ENDPOINTS[endpoint_key]
    if kwargs:
        path = path.format(**kwargs)
    return f"{BASE_URL}{path}"
