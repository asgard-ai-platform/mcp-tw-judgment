# Changelog

## [Unreleased]

### Added
- New `get_judgment_pdf` tool: returns or downloads a judgment's PDF. Behavior controlled by the `save_to` arg or `MCP_TW_JUDGMENT_DOWNLOAD_DIR` env var; when neither is set, only the URL is returned.
- `get_judgment` now returns a `paragraphs` field alongside `content`: a flat list of `{id, section, level, heading, text}` entries with stable hierarchical IDs (e.g. `理由.一.(三).2`) for precise citation and downstream highlighting.

### Changed
- `parser/judgment_parser.py` gains `extract_pdf_url` and `parse_paragraphs`; `parse_detail` now emits `paragraphs` (additive; `content` preserved for backward compatibility).
- `connectors/rest_client.py` gains `api_get_bytes` for binary downloads.

## [0.2.0] - 2026-04-17

### Added
- New tool `lookup_legal_term` — query 司法院裁判書用語辭典 (`/TermContent.aspx`)
  for definitions of a legal term, grouped by 法領域 (民事, 刑事, 行政, 家事).
  Supports an optional `domain` filter to narrow results.
- `parser/terms_parser.py` — pure HTML parser for `TermContent.aspx` responses,
  with offline unit tests (`tests/test_terms_parser.py`) and a saved fixture
  (`tests/fixtures/terms_result.html`).
- `config/settings.py` now exposes `TERMS_BASE_URL` and supports multi-host
  endpoints via the new `base_url=` argument on `connectors/rest_client.api_get_text`.

### Changed
- `connectors/rest_client.py` reintroduces `ServiceAPIError` and a richer
  request helper to support the multi-host setup and graceful 500 handling
  for non-existent terms.

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
