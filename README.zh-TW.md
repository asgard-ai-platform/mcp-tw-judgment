# MCP 台灣裁判書查詢

[![PyPI version](https://img.shields.io/pypi/v/mcp-tw-judgment)](https://pypi.org/project/mcp-tw-judgment/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-tw-judgment)](https://pypi.org/project/mcp-tw-judgment/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io/)
[![GitHub stars](https://img.shields.io/github/stars/asgard-ai-platform/mcp-tw-judgment)](https://github.com/asgard-ai-platform/mcp-tw-judgment/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/asgard-ai-platform/mcp-tw-judgment)](https://github.com/asgard-ai-platform/mcp-tw-judgment/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/asgard-ai-platform/mcp-tw-judgment)](https://github.com/asgard-ai-platform/mcp-tw-judgment/commits/main)

台灣司法院裁判書全文查詢的 MCP 伺服器，透過 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 將查詢功能暴露為 AI 可呼叫的工具。

[English](README.md)

## 功能特色

- **兩個 MCP 工具** — 裁判書全文關鍵字搜尋 + 透過 ID 取得單一裁判書全文
- **stdio JSON-RPC 2.0** — 標準 MCP 傳輸協定
- **`@mcp.tool()` 裝飾器** — Pydantic 型別化工具註冊
- **兩步驟抓取** — 處理司法院網站以 iframe 呈現搜尋結果的特殊架構
- **無需認證** — 司法院裁判書系統為公開端點
- **獨立解析層** — `parser/` 模組與 HTTP 連接器分離，可離線測試（搭配 fixtures）

## 可用工具

| 工具 | 說明 |
|---|---|
| `search_judgments` | 裁判書全文關鍵字搜尋，每頁 20 筆。每筆結果包含 `judgment_id`、標題、裁判日期、案由、URL、與摘要片段。 |
| `get_judgment` | 透過 `judgment_id` 取得單一裁判書的完整內容與基本資料。 |
| `lookup_legal_term` | 查詢司法院裁判書用語辭典，取得法律名詞在各法領域（民事、刑事、行政、家事）的定義。可透過 `domain` 參數篩選特定法領域。 |

## 環境需求

- Python `3.12+`
- [`uv`](https://github.com/astral-sh/uv)（建議）或 `pip`

## 安裝

### 方式 1 — `uvx`（不安裝，按需執行）

```bash
uvx mcp-tw-judgment
```

### 方式 2 — `pip` / `uv pip`

```bash
pip install mcp-tw-judgment
# 或
uv pip install mcp-tw-judgment
```

安裝後可直接使用 `mcp-tw-judgment` 指令。

### 方式 3 — 由原始碼安裝

```bash
git clone https://github.com/asgard-ai-platform/mcp-tw-judgment.git
cd mcp-tw-judgment
uv sync
uv run mcp-tw-judgment
```

## 使用方式

伺服器透過 stdio 走 MCP 協定，依你的 client 加入設定:

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）
或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）:

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

加到專案 `.mcp.json`:

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

## 工具使用範例

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

## 專案結構

```
mcp-tw-judgment/
├── app.py                       # FastMCP 單例
├── mcp_server.py                # 入口（stdio 傳輸）
├── config/settings.py           # API 基礎 URL、端點、請求標頭
├── connectors/rest_client.py    # HTTP GET helper（含重試 + 編碼偵測）
├── auth/none.py                 # 無認證模組（公開 API）
├── parser/
│   ├── judgment_parser.py       # 純 HTML 解析：裁判書（不含 HTTP）
│   └── terms_parser.py          # 純 HTML 解析：用語辭典（不含 HTTP）
├── tools/judgment_tools.py      # MCP 工具定義
├── tests/
│   ├── fixtures/                # 儲存的 HTML 回應（供離線單元測試使用）
│   ├── test_judgment_parser.py  # 單元測試（無需網路）
│   ├── test_terms_parser.py     # 用語辭典解析器單元測試（無需網路）
│   └── test_all_tools.py        # 工具測試（即時 API，需 RUN_LIVE_TESTS=1）
└── scripts/auth/test_connection.py
```

## 開發

```bash
# 安裝依賴
uv sync

# 連線檢查
uv run python scripts/auth/test_connection.py

# 本地啟動伺服器
uv run mcp-tw-judgment

# 離線測試（parser + tool 註冊）
uv run python -m unittest tests.test_judgment_parser tests.test_all_tools -v

# 即時 API 測試（會呼叫司法院端點）
RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v
```

新增工具請見 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 授權

MIT License — 詳見 [LICENSE](LICENSE)。

## 資料來源與使用聲明

本專案直接使用[司法院裁判書系統](https://judgment.judicial.gov.tw/FJUD/default.aspx)的公開查詢介面，**非官方 API**。

> **請注意：** 本工具僅供個人查詢與研究使用。請勿進行大量自動化存取或爬取，以免對司法院伺服器造成負擔。使用前請自行評估是否符合司法院網站的使用條款。
