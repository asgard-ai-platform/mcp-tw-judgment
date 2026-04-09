#!/usr/bin/env python3
import sys
import os

# Import tool modules to trigger @mcp.tool() decorator registration.
# TODO: Replace with your actual tool module imports.
import tools.sample_tools  # noqa: F401

from app import mcp


def main():
    mcp.run()  # Default stdio transport


if __name__ == "__main__":
    main()
