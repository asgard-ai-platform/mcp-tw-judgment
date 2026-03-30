# MCP Server Template

## Overview
This is a template for building MCP (Model Context Protocol) servers that expose AI-callable tools over stdio JSON-RPC 2.0. Part of the Asgard open-source ecosystem.

## Setup
```bash
uv venv && source .venv/bin/activate
uv pip install -e .
```

## Run
```bash
python mcp_server.py
```

## Test
```bash
# Test connection
python scripts/auth/test_connection.py

# Run all tool tests
python tests/test_all_tools.py
```

## Architecture

```
stdio (JSON-RPC 2.0)
  → mcp_server.py (entry point, side-effect imports trigger tool registration)
    → app.py (MCPServer singleton)
      → tools/*_tools.py (@mcp.tool() decorated functions)
        → connectors/*_client.py (data source connectors)
          → auth/*.py (authentication)
            → config/settings.py (endpoints, URL builder)
```

### Key Patterns
- **Singleton**: `app.py` creates the `MCPServer` instance, imported everywhere
- **Decorator registration**: `@mcp.tool()` with Pydantic `Field()` for typed parameters
- **Side-effect imports**: `mcp_server.py` imports tool modules to trigger registration
- **Pluggable connectors**: `connectors/` — REST, RSS, Scraper, MQTT, GraphQL
- **Pluggable auth**: `auth/` — Bearer, API Key, OAuth 2.0, None

### Adding a New Tool
1. Choose the appropriate tool module in `tools/` (or create a new one)
2. Import your connector: `from connectors.rest_client import api_get`
3. Write the tool function with `@mcp.tool()` decorator
4. Add the module import in `mcp_server.py` (if new module)
5. Add a test in `tests/test_all_tools.py`

### Code Conventions
- English for all code, docstrings, and tool descriptions
- Use connector helpers — don't call `requests` directly in tools
- All tools return `dict`
- Use `Pydantic Field()` for parameter descriptions and defaults
