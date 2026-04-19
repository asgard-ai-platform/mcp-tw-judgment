from auth.none import get_auth_headers

# API base URLs
BASE_URL       = "https://judgment.judicial.gov.tw"   # 裁判書系統
TERMS_BASE_URL = "https://terms.judicial.gov.tw"      # 司法院名詞解釋

# Default pagination size
DEFAULT_PER_PAGE = 20

# Environment variable controlling default PDF download directory.
# When unset and tool arg `save_to` is None, get_judgment_pdf returns URL only.
DOWNLOAD_DIR_ENV = "MCP_TW_JUDGMENT_DOWNLOAD_DIR"

# =============================================================================
# Endpoint map
# =============================================================================
# /FJUD/qryresult.aspx  — keyword full-text search (param: akw)
# /FJUD/data.aspx       — single judgment detail (param: id)

ENDPOINTS = {
    # 裁判書系統 (BASE_URL)
    "search": "/FJUD/qryresult.aspx",       # step 1: submit keyword → returns hidQID
    "list":   "/FJUD/qryresultlst.aspx",    # step 2: fetch results via qid (in iframe)
    "detail": "/FJUD/data.aspx",            # single judgment full text
    "pdf":    "/FILES/{court}/{rest}.pdf",  # judgment PDF (court + url-encoded rest)
    # 名詞解釋系統 (TERMS_BASE_URL)
    "terms_lookup": "/TermContent.aspx",    # look up exact term, param: TRMTERM, SYS
}


def get_headers() -> dict:
    """Get request headers (no auth required for public judicial API)."""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    headers.update(get_auth_headers())
    return headers


def get_url(endpoint_key: str, base_url: str = BASE_URL, **kwargs) -> str:
    """Build full URL for an endpoint with optional base URL override.

    Args:
        endpoint_key: Key from ENDPOINTS dict.
        base_url: Override the default BASE_URL (e.g. pass TERMS_BASE_URL).
        **kwargs: Path parameters to substitute.

    Returns:
        Full URL string.

    Raises:
        KeyError: If endpoint_key not found in ENDPOINTS.
    """
    path = ENDPOINTS[endpoint_key]
    if kwargs:
        path = path.format(**kwargs)
    return f"{base_url}{path}"
