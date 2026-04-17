"""MCP tools for 司法院裁判書系統 (judicial judgment search).

Two tools:
  search_judgments — full-text keyword search, paginated 20 results/page
  get_judgment     — fetch full text of a single judgment by ID
"""

from pydantic import Field

from app import mcp
from connectors.rest_client import api_get_text
from parser.judgment_parser import (
    extract_qid,
    parse_detail,
    parse_result_count,
    parse_result_list,
)


@mcp.tool()
def search_judgments(
    keyword: str = Field(description="全文搜尋關鍵字（例如：著作權、詐欺、柯文哲）"),
    page: int = Field(default=1, ge=1, description="頁碼，每頁 20 筆，預設第 1 頁"),
) -> dict:
    """搜尋司法院裁判書全文，回傳符合關鍵字的裁判書清單。

    每筆結果包含 judgment_id（可傳入 get_judgment 取得全文）、標題、裁判日期、
    案由、摘要片段。
    """
    search_html = api_get_text("search", params={"akw": keyword})
    qid = extract_qid(search_html)
    total = parse_result_count(search_html)

    list_html = api_get_text("list", params={"ty": "JUDBOOK", "q": qid, "page": page})
    results = parse_result_list(list_html)

    return {
        "keyword": keyword,
        "total":   total,
        "page":    page,
        "results": results,
    }


@mcp.tool()
def get_judgment(
    judgment_id: str = Field(
        description=(
            "裁判書 ID，可從 search_judgments 結果的 judgment_id 欄位取得。"
            "格式範例：IPCV,114,民著訴,52,20260415,1"
        )
    ),
) -> dict:
    """取得單一裁判書的完整內容，包含案件資訊與全文。"""
    detail_html = api_get_text(
        "detail",
        params={"ty": "JD", "id": judgment_id, "ot": "in"},
    )
    return parse_detail(detail_html)
