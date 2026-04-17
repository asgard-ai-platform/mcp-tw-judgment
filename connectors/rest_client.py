"""HTTP client for the 司法院裁判書 public site.

Single helper used by the tools layer: ``api_get_text`` issues a GET against an
endpoint registered in ``config.settings.ENDPOINTS`` and returns the raw HTML
with auto-detected encoding.
"""

import time

import requests

from config.settings import get_headers, get_url


def api_get_text(
    endpoint_key: str,
    params: dict | None = None,
    path_params: dict | None = None,
    retries: int = 3,
    timeout: int = 60,
) -> str:
    """GET an endpoint and return raw HTML/text with retry on transient errors."""
    url = get_url(endpoint_key, **(path_params or {}))
    headers = get_headers()

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)
