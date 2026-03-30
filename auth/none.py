"""No-op authentication module for public APIs and open data sources."""


def get_auth_headers() -> dict:
    """Return empty headers (no authentication required).

    Returns:
        Empty dict.
    """
    return {}
