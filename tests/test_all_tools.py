#!/usr/bin/env python3
"""E2E test runner for all MCP tools.

Runs each tool with test parameters against the live API.
Requires valid credentials in environment variables.

Usage:
    python tests/test_all_tools.py
"""

import sys
import os
import asyncio
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import tool modules to trigger @mcp.tool() registration
import tools.sample_tools  # noqa: F401

from app import mcp


results = []


def run_test(name: str, fn, **kwargs):
    """Run a single tool test and record the result.

    Args:
        name: Display name for the test.
        fn: Tool function to call.
        **kwargs: Arguments to pass to the tool function.
    """
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    try:
        result = fn(**kwargs)
        print(f"  PASS")
        if isinstance(result, dict):
            for key, value in result.items():
                preview = str(value)
                if len(preview) > 100:
                    preview = preview[:100] + "..."
                print(f"    {key}: {preview}")
        results.append(("PASS", name))
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        results.append(("FAIL", name))


def main():
    # Verify tool count
    tools_list = asyncio.run(mcp.list_tools())
    print(f"Registered tools: {len(tools_list)}")
    for tool in tools_list:
        print(f"  - {tool.name}: {tool.description[:80] if tool.description else 'no description'}")

    print(f"\n{'#'*60}")
    print(f"RUNNING E2E TESTS")
    print(f"{'#'*60}")

    # =========================================================================
    # TODO: Replace with your actual tool tests
    # =========================================================================

    # Test 1: get_item
    # run_test("get_item", tools.sample_tools.get_item, item_id="test-123")

    # Test 2: list_items
    # run_test("list_items", tools.sample_tools.list_items, limit=5)

    # Test 3: get_item_summary
    # run_test("get_item_summary", tools.sample_tools.get_item_summary, days=7)

    # =========================================================================
    # Summary
    # =========================================================================
    print(f"\n{'#'*60}")
    print(f"TEST SUMMARY")
    print(f"{'#'*60}")

    passed = sum(1 for status, _ in results if status == "PASS")
    failed = sum(1 for status, _ in results if status == "FAIL")

    for status, name in results:
        icon = "+" if status == "PASS" else "X"
        print(f"  [{icon}] {name}")

    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
