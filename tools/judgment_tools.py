"""MCP tools for 司法院裁判書系統 (judicial judgment search).

Two tools:
  search_judgments — full-text keyword search, paginated 20 results/page
  get_judgment     — fetch full text of a single judgment by ID
  lookup_legal_term — look up a legal term in 司法院裁判書用語辭典
  get_judgment_pdf  — fetch PDF URL and optionally download to disk
"""

import os
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from pydantic import Field

from app import mcp
from config.settings import BASE_URL, DOWNLOAD_DIR_ENV, TERMS_BASE_URL
from connectors.rest_client import ServiceAPIError, api_get_bytes, api_get_text
from parser.judgment_parser import (
    extract_pdf_url,
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


@mcp.tool()
def get_judgment_pdf(
    judgment_id: Annotated[str, Field(
        description=(
            "裁判書 ID，可從 search_judgments 結果取得。"
            "格式範例：TPDM,114,易,1585,20260326,1"
        )
    )],
    save_to: Annotated[str | None, Field(
        description=(
            "儲存目的。以 .pdf 結尾視為完整檔案路徑；否則視為目錄並用預設檔名 "
            "{judgment_id}.pdf 放入。未指定時讀環境變數 "
            "MCP_TW_JUDGMENT_DOWNLOAD_DIR；若也未設定則不下載，只回 URL。"
        )
    )] = None,
) -> dict:
    """取得裁判書 PDF 連結，可選擇直接下載到本機。

    回傳 dict 一定包含 judgment_id 與 url；當實際下載時另含 path、size_bytes、cached。
    """
    url = _resolve_pdf_url(judgment_id)
    target = _resolve_save_path(save_to, judgment_id)

    if target is None:
        return {"judgment_id": judgment_id, "url": url}

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        return {
            "judgment_id": judgment_id,
            "url":         url,
            "path":        str(target),
            "size_bytes":  target.stat().st_size,
            "cached":      True,
        }

    pdf_bytes = api_get_bytes("pdf", path_params=_pdf_path_params(judgment_id))
    target.write_bytes(pdf_bytes)

    return {
        "judgment_id": judgment_id,
        "url":         url,
        "path":        str(target),
        "size_bytes":  len(pdf_bytes),
        "cached":      False,
    }


# -----------------------------------------------------------------------------
# Helpers for get_judgment_pdf
# -----------------------------------------------------------------------------

def _resolve_pdf_url(judgment_id: str) -> str:
    """Find the PDF URL for a judgment. Prefer the detail page link; fall back
    to constructing the URL from judgment_id.

    Raises ParseError-equivalent via explicit exception when neither yields a URL.
    """
    try:
        detail_html = api_get_text(
            "detail",
            params={"ty": "JD", "id": judgment_id, "ot": "in"},
        )
        extracted = extract_pdf_url(detail_html)
        if extracted:
            return extracted
    except ServiceAPIError:
        pass  # fall through to constructed URL

    # Fallback: construct from judgment_id structure.
    path_params = _pdf_path_params(judgment_id)
    return f"{BASE_URL}/FILES/{path_params['court']}/{path_params['rest']}.pdf"


def _pdf_path_params(judgment_id: str) -> dict:
    """Split judgment_id into {court, rest} for the `pdf` endpoint template.

    judgment_id format: "COURT,YEAR,TYPE,NUM,DATE,SEQ". The first segment is
    the court code; the rest is url-encoded with commas escaped.
    """
    parts = judgment_id.split(",", 1)
    if len(parts) != 2:
        raise ValueError(f"malformed judgment_id: {judgment_id!r}")
    court, rest = parts
    return {"court": court, "rest": quote(rest, safe="")}


def _resolve_save_path(save_to: str | None, judgment_id: str) -> Path | None:
    """Decide where (if anywhere) to save the PDF.

    Precedence: explicit save_to > MCP_TW_JUDGMENT_DOWNLOAD_DIR env > None.
    A path ending in .pdf is treated as a full file path; anything else is a
    directory and the default filename `{judgment_id}.pdf` is appended.
    """
    candidate = save_to if save_to is not None else os.environ.get(DOWNLOAD_DIR_ENV)
    if not candidate:
        return None

    p = Path(candidate).expanduser()
    if p.suffix.lower() == ".pdf":
        return p
    return p / f"{judgment_id}.pdf"
