# MCP Taiwan Judgment Search

[![PyPI version](https://img.shields.io/pypi/v/mcp-tw-judgment)](https://pypi.org/project/mcp-tw-judgment/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-tw-judgment)](https://pypi.org/project/mcp-tw-judgment/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io/)
[![GitHub stars](https://img.shields.io/github/stars/asgard-ai-platform/mcp-tw-judgment)](https://github.com/asgard-ai-platform/mcp-tw-judgment/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/asgard-ai-platform/mcp-tw-judgment)](https://github.com/asgard-ai-platform/mcp-tw-judgment/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/asgard-ai-platform/mcp-tw-judgment)](https://github.com/asgard-ai-platform/mcp-tw-judgment/commits/main)

An MCP server for searching Taiwan judicial judgments, exposing AI-callable tools over [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

[繁體中文](README.zh-TW.md)

## Features

- **Four MCP tools** — full-text search, full-document fetch by ID, PDF download, and legal-term lookup
- **stdio JSON-RPC 2.0** — standard MCP transport protocol
- **`@mcp.tool()` decorator** — Pydantic-typed tool registration
- **Two-step scraping** — handles the judicial site's iframe-based result rendering
- **No-auth public endpoint** — 司法院裁判書系統 is fully public; no API keys required
- **Pure HTML parser layer** — `parser/` is decoupled from HTTP and tested offline with saved fixtures

## Available Tools

| Tool | Description |
|---|---|
| `search_judgments` | Full-text keyword search across all judicial judgments. Paginated 20 per page. Returns `judgment_id`, title, ruling date, case reason, URL, and a text preview per entry. |
| `get_judgment` | Fetch the complete text and metadata of a single judgment by its `judgment_id`. |
| `lookup_legal_term` | Look up a legal term in the 司法院裁判書用語辭典. Returns definitions for each applicable legal domain (民事、刑事、行政、家事). Optionally filter by `domain`. |
| `get_judgment_pdf` | Return or download a judgment's PDF. When `save_to` (arg) or `MCP_TW_JUDGMENT_DOWNLOAD_DIR` (env) is set, the file is saved locally and the path is returned; otherwise only the URL is returned. |

## Requirements

- Python `3.12+`
- One of: [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

## Installation

### Option 1 — `uvx` (no install, runs on demand)

```bash
uvx mcp-tw-judgment
```

### Option 2 — `pip` / `uv pip`

```bash
pip install mcp-tw-judgment
# or
uv pip install mcp-tw-judgment
```

After install, the `mcp-tw-judgment` console script is available.

### Option 3 — From source

```bash
git clone https://github.com/asgard-ai-platform/mcp-tw-judgment.git
cd mcp-tw-judgment
uv sync
uv run mcp-tw-judgment
```

## Usage

The server speaks MCP over stdio. Add it to your client of choice:

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "tw-judgment": {
      "command": "uvx",
      "args": ["mcp-tw-judgment"]
    }
  }
}
```

### Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "tw-judgment": {
      "command": "uvx",
      "args": ["mcp-tw-judgment"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "tw-judgment": {
      "command": "uvx",
      "args": ["mcp-tw-judgment"]
    }
  }
}
```

### Environment Variables

| Variable | Effect |
|---|---|
| `MCP_TW_JUDGMENT_DOWNLOAD_DIR` | Default directory for `get_judgment_pdf` downloads. If unset and the tool's `save_to` arg is `None`, `get_judgment_pdf` returns the URL without downloading. |

## Example Tool Usage

> **You：** 最近有哪些和著作權有關的判決

**AI call：** `tw-judgment - search_judgments (MCP)(keyword: "著作權")`

```
{
  "keyword": "著作權",
  "total":   55265,
  ...
}
```

**Result：** 以下是最近的著作權相關判決（共 55,265 筆，以下列出最新 10 件核心案件）：
```
115.04.15 │ 智慧財產及商業法院   │ 114年民著訴52 │ 侵害著作權有關人格權爭議
...
```

> **You：** 請告訴我 114年民著訴52 的詳細資訊

**AI call：** `tw-judgment - get_judgment (MCP)(judgment_id: "IPCV,114,民著訴,52,20260415,1")`

**Result：** 114年民著訴52 的詳細資訊如下：...

## Project Structure

```
mcp-tw-judgment/
├── app.py                       # FastMCP singleton
├── mcp_server.py                # Entry point (stdio transport)
├── config/settings.py           # API base URL, endpoints, request headers
├── connectors/rest_client.py    # HTTP GET helper with retry + encoding detection
├── auth/none.py                 # No-op auth module (public endpoint)
├── parser/
│   ├── judgment_parser.py       # Pure HTML parsers for judgments (no HTTP)
│   └── terms_parser.py          # Pure HTML parsers for 用語辭典 (no HTTP)
├── tools/judgment_tools.py      # MCP tool definitions
├── tests/
│   ├── fixtures/                # Saved HTML responses for offline unit tests
│   ├── test_judgment_parser.py  # Unit tests (no network)
│   ├── test_terms_parser.py     # Unit tests for terms parser (no network)
│   └── test_all_tools.py        # Tool tests (live API, opt-in via RUN_LIVE_TESTS=1)
└── scripts/auth/test_connection.py
```

## Development

```bash
# Setup
uv sync

# Connection check
uv run python scripts/auth/test_connection.py

# Run server locally
uv run mcp-tw-judgment

# Offline tests (parser + tool registration)
uv run python -m unittest tests.test_judgment_parser tests.test_all_tools -v

# Live API tests (hits 司法院 endpoint)
RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for adding new tools.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Data Source & Disclaimer

This project directly scrapes the [司法院裁判書系統](https://judgment.judicial.gov.tw/FJUD/default.aspx) public search interface — **this is not an official API**.

> **Please note:** This tool is intended for personal research and ad-hoc queries only. Do not use it for bulk automated access or scraping, as this may place undue load on the judicial system's servers. Use at your own discretion and in accordance with the website's terms of use.
