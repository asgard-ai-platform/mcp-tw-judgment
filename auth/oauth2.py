"""OAuth 2.0 client credentials authentication with automatic token refresh."""

import os
import time

import requests

# TODO: Rename to match your service (e.g., META_CLIENT_ID, META_CLIENT_SECRET)
CLIENT_ID_VAR = "SERVICE_CLIENT_ID"
CLIENT_SECRET_VAR = "SERVICE_CLIENT_SECRET"

# TODO: Set to your OAuth token endpoint
TOKEN_URL = "https://api.example.com/oauth/token"

# Token cache
_token_cache = {
    "access_token": None,
    "expires_at": 0,
}


def _get_credentials() -> tuple[str, str]:
    """Get OAuth client credentials from environment.

    Raises:
        RuntimeError: If credentials env vars are not set.
    """
    client_id = os.environ.get(CLIENT_ID_VAR)
    client_secret = os.environ.get(CLIENT_SECRET_VAR)

    if not client_id or not client_secret:
        raise RuntimeError(
            f"Missing OAuth credentials. Set environment variables:\n"
            f"  export {CLIENT_ID_VAR}=your_client_id\n"
            f"  export {CLIENT_SECRET_VAR}=your_client_secret"
        )

    return client_id, client_secret


def _fetch_token() -> str:
    """Fetch a new access token using client credentials grant.

    Returns:
        Access token string.

    Raises:
        RuntimeError: If token request fails.
    """
    client_id, client_secret = _get_credentials()

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OAuth token request failed [{response.status_code}]: {response.text[:500]}"
        )

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise RuntimeError(f"No access_token in response: {data}")

    expires_in = data.get("expires_in", 3600)
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = time.time() + expires_in - 60  # refresh 60s early

    return access_token


def _get_token() -> str:
    """Get a valid access token, refreshing if expired."""
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]
    return _fetch_token()


def get_auth_headers() -> dict:
    """Get Authorization header with OAuth 2.0 Bearer token.

    Returns:
        Dict with Authorization header.
    """
    token = _get_token()
    return {"Authorization": f"Bearer {token}"}
