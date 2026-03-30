# Contributing

Thank you for contributing to this MCP Server!

## Setup

```bash
git clone https://github.com/asgard-ai-platform/mcp-{service}.git
cd mcp-{service}
uv venv && source .venv/bin/activate
uv pip install -e .
cp .env.example .env
# Edit .env with your credentials
```

## Adding a New Tool

1. **Choose module**: Pick an existing file in `tools/` or create a new `tools/{domain}_tools.py`
2. **Import helpers**: `from connectors.rest_client import api_get, fetch_all_pages`
3. **Write the tool**:
   ```python
   from app import mcp
   from pydantic import Field

   @mcp.tool()
   def my_new_tool(
       param: str = Field(description="What this param does"),
   ) -> dict:
       """What this tool does — shown in MCP tools/list."""
       data = api_get("endpoint_key", path_params={"id": param})
       return {"result": data}
   ```
4. **Register**: If you created a new module, add `import tools.{module}  # noqa: F401` in `mcp_server.py`
5. **Test**: Add a test case in `tests/test_all_tools.py`
6. **Verify**: Run `python tests/test_all_tools.py`

## Code Conventions

- English for code, docstrings, and tool descriptions
- Use connector helpers from `connectors/` — never call `requests` directly in tool functions
- All tools return `dict`
- Use Pydantic `Field()` for parameter descriptions
- Only add dependencies that your connector type requires

## Testing

All tests run against the live API:
```bash
python scripts/auth/test_connection.py   # Validate credentials
python tests/test_all_tools.py           # Run all tool tests
```

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/add-new-tool`
3. Make your changes
4. Run tests
5. Submit a PR with a clear description
