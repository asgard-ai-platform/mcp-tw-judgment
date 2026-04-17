# Changelog

## [0.1.0] - 2026-04-17

### Added
- MCP server exposing two tools over stdio JSON-RPC 2.0:
  - `search_judgments` — full-text keyword search against 司法院裁判書系統, paginated 20 results per page
  - `get_judgment` — fetch the full text and metadata of a single judgment by ID
- Two-step scraping flow that handles the judicial site's iframe-based result rendering
- Pure HTML parser layer (`parser/judgment_parser.py`) decoupled from HTTP
- Offline unit tests with saved HTML fixtures (`tests/fixtures/`)
- Opt-in live API tests via `RUN_LIVE_TESTS=1`
- Connection test script (`scripts/auth/test_connection.py`)
