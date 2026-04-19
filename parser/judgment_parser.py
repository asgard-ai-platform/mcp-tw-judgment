"""Pure HTML parsers for 司法院裁判書系統.

All functions are stateless: they take an HTML string and return structured data.
No HTTP calls here — fetching is handled by connectors/rest_client.py.
"""

import re
from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup

from config.settings import BASE_URL


class ParseError(Exception):
    """Raised when expected content cannot be found in the HTML."""


def extract_qid(search_html: str) -> str:
    """Extract the query ID (hidQID) from the search result page.

    The search page embeds a QID in a hidden input and in the iframe src.
    This QID is required to fetch the actual result list.

    Args:
        search_html: Raw HTML of /FJUD/qryresult.aspx response.

    Returns:
        QID hex string (e.g. "35136288da1b7d1ff241bcfa37be35b9").

    Raises:
        ParseError: If hidQID is not found in the HTML.
    """
    match = re.search(r'name="hidQID"[^>]+value="([a-f0-9]+)"', search_html)
    if not match:
        raise ParseError("hidQID not found in search page HTML")
    return match.group(1)


def parse_result_count(search_html: str) -> int | None:
    """Extract total result count from the search page badge.

    Args:
        search_html: Raw HTML of /FJUD/qryresult.aspx response.

    Returns:
        Integer count, or None if not found.
    """
    match = re.search(r'<span class="badge">(\d+)</span>', search_html)
    return int(match.group(1)) if match else None


def parse_result_list(list_html: str) -> list[dict]:
    """Parse judgment entries from the result list page (iframe content).

    Table structure (table.jub-table):
      - Rows alternate: main row (td[0]=序號, td[1]=標題+link, td[2]=日期, td[3]=案由)
        followed by a summary row (class="summary") with a text preview.
      - Header row contains no <td>, only <th>.

    Args:
        list_html: Raw HTML of /FJUD/qryresultlst.aspx response.

    Returns:
        List of dicts with keys:
        - title: court name + case number + judgment type (size stripped)
        - date: ruling date string (ROC calendar, e.g. "115.04.15")
        - case_reason: case reason/type (裁判案由)
        - url: relative URL to full judgment text (e.g. "data.aspx?ty=JD&id=...")
        - summary: one-sentence preview snippet (may be empty)
    """
    soup = BeautifulSoup(list_html, "html.parser")
    table = soup.select_one("table.jub-table")
    if not table:
        return []

    rows = table.find_all("tr")
    results = []
    pending_summary = ""

    for tr in rows:
        # Summary row — attach to the last parsed entry
        if "summary" in (tr.get("class") or []):
            if results:
                results[-1]["summary"] = tr.get_text(" ", strip=True)
            pending_summary = ""
            continue

        cells = tr.find_all("td")
        if len(cells) < 4:
            continue  # header row or malformed

        link_tag = cells[1].find("a", href=True)
        title_text = re.sub(r"\s*（\d+K）", "", cells[1].get_text(" ", strip=True))
        href = link_tag["href"] if link_tag else ""
        judgment_id = _extract_id_from_href(href)

        results.append({
            "judgment_id": judgment_id,
            "title":       title_text,
            "date":        cells[2].get_text(strip=True),
            "case_reason": cells[3].get_text(strip=True),
            "url":         href,
            "summary":     "",
        })

    return results


# =============================================================================
# Detail page
# =============================================================================

def parse_detail(detail_html: str) -> dict:
    """Parse a single judgment's metadata and full text.

    Metadata is in div#jud (int-table); each row has a div.col-th label and
    div.col-td value. Content body is in div.htmlcontent.

    Args:
        detail_html: Raw HTML of /FJUD/data.aspx response.

    Returns:
        Dict with keys:
        - title: full case title (court + year + case number + type)
        - date: ruling date in ROC calendar (e.g. "民國 115 年 04 月 15 日")
        - case_reason: 裁判案由
        - content: full judgment text (newline-separated paragraphs)
    """
    soup = BeautifulSoup(detail_html, "html.parser")

    meta = soup.select_one("div#jud")
    col_td = meta.select("div.col-td") if meta else []
    title       = col_td[0].get_text(" ", strip=True) if len(col_td) > 0 else ""
    date        = col_td[1].get_text(" ", strip=True) if len(col_td) > 1 else ""
    case_reason = col_td[2].get_text(" ", strip=True) if len(col_td) > 2 else ""

    body = soup.select_one("div.htmlcontent")
    content = body.get_text("\n", strip=True) if body else ""

    return {
        "title":       title,
        "date":        date,
        "case_reason": case_reason,
        "content":     content,
    }


def extract_pdf_url(detail_html: str) -> str | None:
    """Find the judgment's PDF download link in detail-page HTML.

    The detail page carries an <a> pointing to /FILES/<court>/<id>.pdf.
    We return it as an absolute URL on BASE_URL, or None if absent.

    Args:
        detail_html: Raw HTML of /FJUD/data.aspx response.

    Returns:
        Absolute URL string, or None if no PDF link found.
    """
    match = re.search(r'href="(/FILES/[^"]+\.pdf)"', detail_html, re.IGNORECASE)
    if not match:
        return None
    return f"{BASE_URL}{match.group(1)}"


# =============================================================================
# Internal helpers
# =============================================================================

def _extract_id_from_href(href: str) -> str:
    """Extract the judgment ID from a relative detail URL.

    E.g. "data.aspx?ty=JD&id=IPCV%2c114%2c...&ot=in" → "IPCV,114,民著訴,..."
    Returns empty string if id param is absent.
    """
    qs = parse_qs(urlparse(href).query)
    ids = qs.get("id", [])
    return unquote(ids[0]) if ids else ""
