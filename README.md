# MCP Taiwan Judgment Search

An MCP server for searching Taiwan judicial judgments, exposing AI-callable tools over [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

[繁體中文](README.zh-TW.md)

## Features

- **stdio JSON-RPC 2.0** — Standard MCP transport protocol
- **`@mcp.tool()` decorator** — Pydantic-typed tool registration
- **Two-step scraping** — Handles the judicial site's iframe-based result rendering
- **No-auth public API access** — 司法院裁判書系統 is a public endpoint
- **HTML parsing layer** — Dedicated `parser/` module separate from HTTP connectors

## Requirements

- Python `3.12`
- `uv`

## Available Tools

- `search_judgments` — Full-text keyword search across all judicial judgments, paginated 20 results per page. Returns `judgment_id`, title, ruling date, case reason, and a text preview per entry.
- `get_judgment` — Fetch the complete text and metadata of a single judgment by its `judgment_id`.

## Quick Start

```bash
# Setup
uv sync

# Test connection
uv run python scripts/auth/test_connection.py

# Run server
uv run mcp-tw-judgment
```

## Project Structure

```
mcp-tw-judgment/
├── app.py                       # MCPServer singleton
├── mcp_server.py                # Entry point (stdio transport)
├── config/settings.py           # API base URL, endpoints, request headers
├── connectors/
│   └── rest_client.py           #   HTTP REST with retry, text/JSON response modes
├── auth/
│   └── none.py                  #   No auth (public API)
├── parser/
│   └── judgment_parser.py       #   Pure HTML parsers (no HTTP)
├── tools/
│   └── judgment_tools.py        #   MCP tool definitions
├── tests/
│   ├── fixtures/                #   Saved HTML responses for offline unit tests
│   ├── test_judgment_parser.py  #   Unit tests (no network)
│   └── test_all_tools.py        #   Tool tests (live API, opt-in)
└── scripts/auth/test_connection.py
```

## Testing

```bash
# Unit tests — no network required
uv run python -m unittest tests.test_judgment_parser -v

# Tool registration tests — no network required
uv run python -m unittest tests.test_all_tools -v

# Live API tests — hits 司法院 endpoint
RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Data Source & Disclaimer

This project directly scrapes the [司法院裁判書系統](https://judgment.judicial.gov.tw/FJUD/default.aspx) public search interface — **this is not an official API**.

> **Please note:** This tool is intended for personal research and ad-hoc queries only. Do not use it for bulk automated access or scraping, as this may place undue load on the judicial system's servers. Use at your own discretion and in accordance with the website's terms of use.
