"""API key authentication module (header-based or query param)."""

import os

# TODO: Rename to match your service (e.g., ECPAY_API_KEY)
ENV_VAR_NAME = "SERVICE_API_KEY"

# TODO: Set to the header name your API expects (e.g., "X-API-Key", "Api-Key")
HEADER_NAME = "X-API-Key"

# Set to True if the API expects the key as a query parameter instead of a header.
# If True, use get_auth_params() instead of get_auth_headers() in settings.py.
USE_QUERY_PARAM = False
QUERY_PARAM_NAME = "api_key"


def _get_api_key() -> str:
    """Get the API key from environment.

    Raises:
        RuntimeError: If the API key env var is not set.
    """
    key = os.environ.get(ENV_VAR_NAME)
    if not key:
        raise RuntimeError(
            f"Missing API key. Set the {ENV_VAR_NAME} environment variable.\n"
            f"  export {ENV_VAR_NAME}=your_api_key_here"
        )
    return key


def get_auth_headers() -> dict:
    """Get auth headers with API key.

    Returns:
        Dict with API key header. Empty dict if using query param mode.
    """
    if USE_QUERY_PARAM:
        return {}
    return {HEADER_NAME: _get_api_key()}


def get_auth_params() -> dict:
    """Get auth query parameters with API key.

    Returns:
        Dict with API key query param. Empty dict if using header mode.
    """
    if not USE_QUERY_PARAM:
        return {}
    return {QUERY_PARAM_NAME: _get_api_key()}
