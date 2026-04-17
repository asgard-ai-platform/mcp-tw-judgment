"""MCP tools for 司法院裁判書系統 (judicial judgment search).

Two tools:
  search_judgments — full-text keyword search, paginated 20 results/page
  get_judgment     — fetch full text of a single judgment by ID
  lookup_legal_term — look up a legal term in 司法院裁判書用語辭典
"""

from typing import Annotated

from pydantic import Field

from app import mcp
from config.settings import TERMS_BASE_URL
from connectors.rest_client import ServiceAPIError, api_get_text
from parser.judgment_parser import (
    extract_qid,
    parse_detail,
    parse_result_count,
    parse_result_list,
)
from parser.terms_parser import parse_term_definitions


@mcp.tool()
def search_judgments(
    keyword: Annotated[str, Field(description="全文搜尋關鍵字（例如：著作權、詐欺、柯文哲）")],
    page: Annotated[int, Field(ge=1, description="頁碼，每頁 20 筆，預設第 1 頁")] = 1,
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
    judgment_id: Annotated[str, Field(
        description=(
            "裁判書 ID，可從 search_judgments 結果的 judgment_id 欄位取得。"
            "格式範例：IPCV,114,民著訴,52,20260415,1"
        )
    )],
) -> dict:
    """取得單一裁判書的完整內容，包含案件資訊與全文。"""
    detail_html = api_get_text(
        "detail",
        params={"ty": "JD", "id": judgment_id, "ot": "in"},
    )
    return parse_detail(detail_html)


@mcp.tool()
def lookup_legal_term(
    term: Annotated[str, Field(description="查詢的法律名詞（例如：比例原則、善意第三人、消滅時效）")],
    domain: Annotated[str | None, Field(description="篩選法領域，例如：民事、刑事、行政、家事。不填則回傳所有領域。")] = None,
) -> dict:
    """查詢司法院裁判書用語辭典，取得法律名詞的定義與各法領域說明。

    同一名詞可能有民事、刑事、行政、家事等不同法領域的解釋，均會一併回傳。
    指定 domain 可篩選特定法領域的解釋。
    """
    try:
        html = api_get_text(
            "terms_lookup",
            params={"TRMTERM": term, "SYS": "V"},
            base_url=TERMS_BASE_URL,
        )
    except ServiceAPIError as e:
        if e.status_code == 500:
            return {"term": term, "definitions": [], "disclaimer": ""}
        raise
    result = parse_term_definitions(html)

    if domain:
        result["definitions"] = [
            d for d in result["definitions"] if d["domain"] == domain
        ]

    return result
