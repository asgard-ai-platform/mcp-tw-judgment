import os

from auth.none import get_auth_headers

# API base URL — 司法院全文檢索系統
BASE_URL = "https://judgment.judicial.gov.tw"

# Default pagination size
DEFAULT_PER_PAGE = 20

# =============================================================================
# Endpoint map
# =============================================================================
# /FJUD/qryresult.aspx  — keyword full-text search (param: akw)
# /FJUD/data.aspx       — single judgment detail (param: id)

ENDPOINTS = {
    "search": "/FJUD/qryresult.aspx",       # step 1: submit keyword → returns hidQID
    "list":   "/FJUD/qryresultlst.aspx",    # step 2: fetch results via qid (in iframe)
    "detail": "/FJUD/data.aspx",            # single judgment full text
}


def get_headers() -> dict:
    """Get request headers (no auth required for public judicial API)."""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
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
