"""Bearer token authentication module."""

import os

# TODO: Rename to match your service (e.g., SHOPLINE_API_TOKEN)
ENV_VAR_NAME = "SERVICE_API_TOKEN"


def get_auth_headers() -> dict:
    """Get Authorization header with Bearer token.

    Returns:
        Dict with Authorization header.

    Raises:
        RuntimeError: If the token env var is not set.
    """
    token = os.environ.get(ENV_VAR_NAME)
    if not token:
        raise RuntimeError(
            f"Missing API token. Set the {ENV_VAR_NAME} environment variable.\n"
            f"  export {ENV_VAR_NAME}=your_token_here"
        )
    return {"Authorization": f"Bearer {token}"}
