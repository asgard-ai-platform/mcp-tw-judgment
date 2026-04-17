# Contributing

Thanks for contributing to `mcp-tw-judgment`!

## Setup

```bash
git clone https://github.com/asgard-ai-platform/mcp-tw-judgment.git
cd mcp-tw-judgment
uv sync
```

## Adding a New Tool

1. **Choose module**: extend `tools/judgment_tools.py` or create a new `tools/{domain}_tools.py`
2. **Import helpers**:
   ```python
   from app import mcp
   from connectors.rest_client import api_get_text
   from parser.judgment_parser import parse_result_list  # or your own parser
   from pydantic import Field
   ```
3. **Write the tool**:
   ```python
   @mcp.tool()
   def my_new_tool(
       param: str = Field(description="What this param does"),
   ) -> dict:
       """What this tool does — shown in MCP tools/list."""
       html = api_get_text("search", params={"akw": param})
       return {"results": parse_result_list(html)}
   ```
4. **Register**: if you create a new module, add `import tools.{module}  # noqa: F401` in `mcp_server.py`
5. **Test**: add a test case in `tests/test_all_tools.py`. Mark API-hitting tests with `@live`
6. **Verify**:
   ```bash
   uv run python -m unittest tests.test_all_tools -v
   RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v
   ```

## Code Conventions

- English for code, docstrings, and tool descriptions; Chinese is fine for
  user-facing strings (parameter descriptions, tool docstrings shown to the LLM)
- All tools return `dict`
- Use Pydantic `Field()` for parameter descriptions and defaults
- HTTP calls go through `connectors/rest_client.py` — never call `requests`
  directly from tools or parsers
- Parsers are pure functions: HTML string in, structured dict out. No HTTP.

## Testing

```bash
# Offline unit tests (parser + tool registration) — no network
uv run python -m unittest tests.test_judgment_parser -v
uv run python -m unittest tests.test_all_tools -v

# Live API tests — hits 司法院 endpoint
RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v

# Connection check
uv run python scripts/auth/test_connection.py
```

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-change`
3. Run tests
4. Submit a PR with a clear description
