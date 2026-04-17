#!/usr/bin/env python3
"""Test connection to the judicial judgment search system.

Verifies that the 司法院全文檢索 endpoint is reachable and returns results.

Usage:
    python scripts/auth/test_connection.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import get_headers, get_url, BASE_URL


TEST_KEYWORD = "著作權"


def check_connection():
    """Test reachability of the judgment search endpoint."""
    import requests

    url = get_url("search")
    print(f"Testing connection to {url} ...")

    try:
        response = requests.get(
            url,
            headers=get_headers(),
            params={"akw": TEST_KEYWORD},
            timeout=15,
        )

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            content_length = len(response.text)
            has_results = "jud" in response.text.lower() or "裁判" in response.text
            print(f"  OK: Response received ({content_length:,} bytes).")
            print(f"  Results present: {'yes' if has_results else 'no (empty or unexpected HTML)'}")
            return True
        else:
            print(f"  FAIL: Unexpected status code {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  FAIL: Cannot connect to {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        print("  FAIL: Connection timed out.")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def main():
    print("=" * 50)
    print("MCP Server — Connection Test")
    print(f"Target: {BASE_URL}")
    print("=" * 50)

    ok = check_connection()
    if not ok:
        print("\nConnection test failed.")
        sys.exit(1)

    print("\nAll checks passed. Ready to use.")


if __name__ == "__main__":
    main()
