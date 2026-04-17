# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

MCP server for searching Taiwan judicial judgments via [司法院裁判書系統](https://judgment.judicial.gov.tw/FJUD/default.aspx). Exposes two tools over stdio JSON-RPC 2.0: `search_judgments` and `get_judgment`.

## Commands

```bash
# Setup
uv sync

# Run server
uv run mcp-tw-judgment

# Test API connectivity
uv run python scripts/auth/test_connection.py

# Unit tests (no network)
uv run python -m unittest tests.test_judgment_parser -v

# Tool registration tests (no network)
uv run python -m unittest tests.test_all_tools -v

# Live API tests
RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v
```

After editing `mcp_server.py`, run `uv sync --reinstall-package mcp-tw-judgment` to update the installed entry point.

## Architecture

```
stdio (JSON-RPC 2.0)
  → mcp_server.py          side-effect import triggers tool registration
    → app.py               FastMCP singleton
      → tools/judgment_tools.py   @mcp.tool() definitions
          → connectors/rest_client.py   api_get_text() fetches raw HTML
          → parser/judgment_parser.py   pure HTML → structured data
            → config/settings.py        BASE_URL, ENDPOINTS, headers
```

### Key Patterns

- **Singleton**: `app.py` creates the `FastMCP` instance; all modules import from it
- **Side-effect import**: `mcp_server.py` imports tool modules to trigger `@mcp.tool()` registration
- **Two-step fetch**: `search_judgments` sends `GET /FJUD/qryresult.aspx?akw=…` → parses `hidQID` → fetches `GET /FJUD/qryresultlst.aspx?ty=JUDBOOK&q={qid}&page={n}` (the iframe content)
- **Parser layer**: `parser/judgment_parser.py` is pure functions (HTML string in, structured data out). No HTTP calls. Tested offline with fixtures in `tests/fixtures/`
- **`@live` decorator**: in `tests/test_all_tools.py`, wraps `unittest.skipUnless(os.environ.get("RUN_LIVE_TESTS"), …)`

### Code Conventions

- All tools return `dict`
- Use `Pydantic Field()` for parameter descriptions and defaults
- HTTP calls go through `connectors/rest_client.py` — do not call `requests` directly in tools or parsers
- `response_format="text"` on `api_get_text()` auto-detects encoding for HTML responses
