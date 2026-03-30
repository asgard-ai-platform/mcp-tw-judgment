# MCP Server Template

A reusable template for building [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers that expose AI-callable tools. Part of the [Asgard AI Platform](https://github.com/asgard-ai-platform) open-source ecosystem.

[繁體中文](README.zh-TW.md)

## Features

- **stdio JSON-RPC 2.0** — Standard MCP transport protocol
- **`@mcp.tool()` decorator** — Pydantic-typed tool registration
- **Pluggable connectors** — REST, RSS, Scraper, MQTT, GraphQL
- **Pluggable auth** — Bearer token, API key, OAuth 2.0, No auth
- **E2E testing** — Live API test runner
- **Claude Code integration** — `.mcp.json` auto-discovery + `CLAUDE.md`

## How to Use This Template

1. Click **"Use this template"** on GitHub (or fork this repo)
2. Rename to `mcp-{your-service}` (e.g., `mcp-ecpay`)
3. **Choose your connector** — keep the one you need in `connectors/`, delete the rest
4. **Choose your auth** — keep the one you need in `auth/`, delete the rest
5. **Configure** — update `config/settings.py` with your API endpoints
6. **Build tools** — replace `tools/sample_tools.py` with your real tools
7. **Update metadata** — `pyproject.toml`, `.mcp.json`, `.env.example`, READMEs

## Quick Start

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e .

# Configure credentials
cp .env.example .env
# Edit .env with your API credentials

# Test connection
python scripts/auth/test_connection.py

# Run server
python mcp_server.py
```

## Project Structure

```
mcp-{service}/
├── app.py                  # MCPServer singleton
├── mcp_server.py           # Entry point (stdio transport)
├── config/settings.py      # API endpoints, URL builder, auth delegation
├── connectors/             # Data source connectors (pick one)
│   ├── rest_client.py      #   HTTP REST with retry + pagination
│   ├── rss_client.py       #   RSS/Atom feed parser
│   ├── scraper_client.py   #   Web scraper with BeautifulSoup
│   ├── mqtt_client.py      #   MQTT for IoT/industrial
│   └── graphql_client.py   #   GraphQL with relay pagination
├── auth/                   # Authentication modules (pick one)
│   ├── bearer.py           #   Bearer token
│   ├── api_key.py          #   API key (header or query param)
│   ├── oauth2.py           #   OAuth 2.0 client credentials
│   └── none.py             #   No auth (public APIs)
├── tools/                  # Your MCP tools
│   └── sample_tools.py     #   Example tools (replace these)
├── tests/test_all_tools.py # E2E test runner
└── scripts/auth/test_connection.py
```

## Connectors

| Connector | Use Case | Extra Dependencies |
|-----------|----------|-------------------|
| `rest_client.py` | REST APIs (majority of services) | None (uses `requests`) |
| `rss_client.py` | RSS/Atom feeds (news, blogs) | `feedparser` |
| `scraper_client.py` | Web scraping (forums, public pages) | `beautifulsoup4` |
| `mqtt_client.py` | IoT/Industrial (MQTT brokers) | `paho-mqtt` |
| `graphql_client.py` | GraphQL APIs (Meta, etc.) | None (uses `requests`) |

## Auth Modules

| Module | Pattern | Env Variables |
|--------|---------|---------------|
| `bearer.py` | `Authorization: Bearer <token>` | `SERVICE_API_TOKEN` |
| `api_key.py` | Header or query param | `SERVICE_API_KEY` |
| `oauth2.py` | Client credentials + auto-refresh | `SERVICE_CLIENT_ID`, `SERVICE_CLIENT_SECRET` |
| `none.py` | No authentication | (none) |

## Adding a Tool

```python
from app import mcp
from pydantic import Field
from connectors.rest_client import api_get

@mcp.tool()
def get_order(
    order_id: str = Field(description="The order ID to look up"),
) -> dict:
    """Get details of a specific order."""
    return api_get("order_detail", path_params={"order_id": order_id})
```

## Testing

```bash
python scripts/auth/test_connection.py   # Validate credentials
python tests/test_all_tools.py           # Run all tool E2E tests
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Part of the Asgard Ecosystem

This template powers 63+ MCP servers connecting AI to real-world services across e-commerce, finance, government data, IoT, social media, and more. See the full [Asgard AI Platform](https://github.com/asgard-ai-platform).
