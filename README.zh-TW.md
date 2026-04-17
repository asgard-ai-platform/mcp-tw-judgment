# MCP 台灣裁判書查詢

台灣司法院裁判書全文查詢的 MCP 伺服器，透過 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 將查詢功能暴露為 AI 可呼叫的工具。

[English](README.md)

## 功能特色

- **stdio JSON-RPC 2.0** — 標準 MCP 傳輸協定
- **`@mcp.tool()` 裝飾器** — Pydantic 型別化工具註冊
- **兩步驟抓取** — 處理司法院網站以 iframe 呈現搜尋結果的特殊架構
- **無需認證** — 司法院裁判書系統為公開端點
- **獨立解析層** — `parser/` 模組與 HTTP 連接器分離

## 環境需求

- Python `3.12`
- `uv`

## 可用工具

- `search_judgments` — 裁判書全文關鍵字搜尋，每頁回傳 20 筆。每筆結果包含 `judgment_id`、標題、裁判日期、案由與文字預覽。
- `get_judgment` — 透過 `judgment_id` 取得單一裁判書的完整內容與基本資料。

## 快速開始

```bash
# 環境設定
uv sync

# 測試連線
uv run python scripts/auth/test_connection.py

# 啟動伺服器
uv run mcp-tw-judgment
```

## 專案結構

```
mcp-tw-judgment/
├── app.py                       # MCPServer 單例
├── mcp_server.py                # 入口（stdio 傳輸）
├── config/settings.py           # API 基礎 URL、端點、請求標頭
├── connectors/
│   └── rest_client.py           #   HTTP REST（含重試、text/JSON 回應模式）
├── auth/
│   └── none.py                  #   無認證（公開 API）
├── parser/
│   └── judgment_parser.py       #   純 HTML 解析（不含 HTTP）
├── tools/
│   └── judgment_tools.py        #   MCP 工具定義
├── tests/
│   ├── fixtures/                #   儲存的 HTML 回應（供離線單元測試使用）
│   ├── test_judgment_parser.py  #   單元測試（無需網路）
│   └── test_all_tools.py        #   工具測試（即時 API，需手動啟用）
└── scripts/auth/test_connection.py
```

## 測試

```bash
# 單元測試 — 無需網路
uv run python -m unittest tests.test_judgment_parser -v

# 工具註冊測試 — 無需網路
uv run python -m unittest tests.test_all_tools -v

# 即時 API 測試 — 會呼叫司法院端點
RUN_LIVE_TESTS=1 uv run python -m unittest tests.test_all_tools -v
```

## 授權

MIT License — 詳見 [LICENSE](LICENSE)。

## 資料來源與使用聲明

本專案直接使用[司法院裁判書系統](https://judgment.judicial.gov.tw/FJUD/default.aspx)的公開查詢介面，**非官方 API**。

> **請注意：** 本工具僅供個人查詢與研究使用。請勿進行大量自動化存取或爬取，以免對司法院伺服器造成負擔。使用前請自行評估是否符合司法院網站的使用條款。
