# MCP Server 範本

建構 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 伺服器的可重用範本，將 AI 可呼叫的工具暴露給 AI 客戶端。[Asgard AI Platform](https://github.com/asgard-ai-platform) 開源生態系的一部分。

[English](README.md)

## 功能特色

- **stdio JSON-RPC 2.0** — 標準 MCP 傳輸協定
- **`@mcp.tool()` 裝飾器** — Pydantic 型別化工具註冊
- **可插拔連接器** — REST、RSS、Scraper、MQTT、GraphQL
- **可插拔認證** — Bearer Token、API Key、OAuth 2.0、無認證
- **E2E 測試** — 即時 API 測試執行器
- **Claude Code 整合** — `.mcp.json` 自動發現 + `CLAUDE.md`

## 如何使用此範本

1. 在 GitHub 上點擊 **「Use this template」**（或 Fork 此 Repo）
2. 重新命名為 `mcp-{你的服務}` （例如 `mcp-ecpay`）
3. **選擇連接器** — 保留 `connectors/` 中需要的，刪除其餘
4. **選擇認證** — 保留 `auth/` 中需要的，刪除其餘
5. **設定** — 更新 `config/settings.py` 的 API 端點
6. **建構工具** — 用你的實際工具替換 `tools/sample_tools.py`
7. **更新元資料** — `pyproject.toml`、`.mcp.json`、`.env.example`、README

## 快速開始

```bash
# 環境設定
uv venv && source .venv/bin/activate
uv pip install -e .

# 設定認證
cp .env.example .env
# 編輯 .env 填入你的 API 認證資訊

# 測試連線
python scripts/auth/test_connection.py

# 啟動伺服器
python mcp_server.py
```

## 專案結構

```
mcp-{service}/
├── app.py                  # MCPServer 單例
├── mcp_server.py           # 入口（stdio 傳輸）
├── config/settings.py      # API 端點、URL 建構、認證委派
├── connectors/             # 資料來源連接器（選一個）
│   ├── rest_client.py      #   HTTP REST（含重試＋分頁）
│   ├── rss_client.py       #   RSS/Atom 訂閱解析
│   ├── scraper_client.py   #   網頁爬取（BeautifulSoup）
│   ├── mqtt_client.py      #   MQTT（IoT / 工業）
│   └── graphql_client.py   #   GraphQL（Relay 分頁）
├── auth/                   # 認證模組（選一個）
│   ├── bearer.py           #   Bearer Token
│   ├── api_key.py          #   API Key（Header 或 Query Param）
│   ├── oauth2.py           #   OAuth 2.0 客戶端憑證
│   └── none.py             #   無認證（公開 API）
├── tools/                  # 你的 MCP 工具
│   └── sample_tools.py     #   範例工具（請替換）
├── tests/test_all_tools.py # E2E 測試執行器
└── scripts/auth/test_connection.py
```

## 連接器

| 連接器 | 用途 | 額外依賴 |
|--------|------|----------|
| `rest_client.py` | REST API（大多數服務） | 無（使用 `requests`） |
| `rss_client.py` | RSS/Atom 訂閱（新聞、部落格） | `feedparser` |
| `scraper_client.py` | 網頁爬取（論壇、公開頁面） | `beautifulsoup4` |
| `mqtt_client.py` | IoT / 工業（MQTT Broker） | `paho-mqtt` |
| `graphql_client.py` | GraphQL API（Meta 等） | 無（使用 `requests`） |

## 認證模組

| 模組 | 模式 | 環境變數 |
|------|------|----------|
| `bearer.py` | `Authorization: Bearer <token>` | `SERVICE_API_TOKEN` |
| `api_key.py` | Header 或 Query Param | `SERVICE_API_KEY` |
| `oauth2.py` | 客戶端憑證 + 自動刷新 | `SERVICE_CLIENT_ID`、`SERVICE_CLIENT_SECRET` |
| `none.py` | 無認證 | （無） |

## 新增工具

```python
from app import mcp
from pydantic import Field
from connectors.rest_client import api_get

@mcp.tool()
def get_order(
    order_id: str = Field(description="要查詢的訂單 ID"),
) -> dict:
    """取得特定訂單的詳細資訊。"""
    return api_get("order_detail", path_params={"order_id": order_id})
```

## 測試

```bash
python scripts/auth/test_connection.py   # 驗證認證資訊
python tests/test_all_tools.py           # 執行所有工具 E2E 測試
```

## 授權

MIT License — 詳見 [LICENSE](LICENSE)。

## Asgard 生態系

此範本驅動 63+ 個 MCP 伺服器，連接 AI 至電商、金融、政府開放資料、IoT、社群媒體等真實世界服務。查看完整 [Asgard AI Platform](https://github.com/asgard-ai-platform)。
