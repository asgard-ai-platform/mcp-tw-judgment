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
        - paragraphs: list of {id, section, level, heading, text} dicts
          (see parse_paragraphs for details)
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
        "paragraphs":  parse_paragraphs(detail_html),
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
# Paragraph structuring
# =============================================================================

# Section headers that can appear on their own line at the top of a part.
# Matching is done after stripping all whitespace/NBSP from the line.
_SECTION_NAMES = ("主文", "事實及理由", "事實", "理由")

# Lines that mark the start of appendix/footer material (附註, 附圖, 附表).
# When one of these is encountered, structural parsing stops and subsequent
# lines are simply appended as plain text to the last paragraph.
_FOOTER_SENTINELS = frozenset({"附註：", "附圖：", "附表："})

# Level 2: 一、二、三、…十、一百、
_RE_LEVEL2 = re.compile(r"^([一二三四五六七八九十百零]+)\s*、\s*(.*)$")
# Level 3a: (一)(二)… or （一）（二）…
_RE_LEVEL3_PAREN = re.compile(r"^[（(]\s*([一二三四五六七八九十百零]+)\s*[）)]\s*(.*)$")
# Level 3b: ㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩ (Unicode circled CJK numbers U+3220–U+3229)
_CIRCLED_TO_HANZI = {
    "㈠": "一", "㈡": "二", "㈢": "三", "㈣": "四", "㈤": "五",
    "㈥": "六", "㈦": "七", "㈧": "八", "㈨": "九", "㈩": "十",
}
_RE_LEVEL3_CIRCLED = re.compile(r"^([㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩])\s*(.*)$")
# Level 4: 1. 2、 etc. (Arabic number followed by . or 、)
_RE_LEVEL4 = re.compile(r"^(\d+)\s*[.、]\s*(.*)$")


def _normalize_ws(s: str) -> str:
    """Strip all whitespace and non-breaking spaces from a string."""
    return re.sub(r"[\xa0\u3000\s]+", "", s)


def parse_paragraphs(detail_html: str) -> list[dict]:
    """Split judgment body into a flat list of hierarchically-identified paragraphs.

    Each entry carries a stable ``id`` (e.g. ``"事實及理由.一.(三).2"``) so
    downstream consumers (LLMs, highlighters) can reference specific segments.

    Non-matching lines are merged into the running paragraph's ``text``.
    When no section header is detected at all, the entire body is returned
    as a single ``{"id": "全文", "section": "全文", "level": 1, ...}`` entry.

    Args:
        detail_html: Raw HTML of /FJUD/data.aspx response.

    Returns:
        List of ``{id, section, level, heading, text}`` dicts in document order.
    """
    soup = BeautifulSoup(detail_html, "html.parser")
    body = soup.select_one("div.htmlcontent")
    if not body:
        return []

    # Preserve line breaks so each structural cue is its own line.
    raw = body.get_text("\n", strip=True)
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if not lines:
        return []

    paragraphs: list[dict] = []
    section: str | None = None
    seen_sections: set[str] = set()
    current_l2_id: str | None = None
    current_l3_id: str | None = None
    in_footer: bool = False  # True once an appendix/footer sentinel is encountered

    def _emit(p: dict) -> None:
        paragraphs.append(p)

    def _append_to_last(text: str) -> None:
        if paragraphs:
            prev = paragraphs[-1]
            prev["text"] = (prev["text"] + " " + text).strip() if prev["text"] else text

    for line in lines:
        # Once we enter appendix/footer territory, skip structural parsing.
        if line in _FOOTER_SENTINELS:
            in_footer = True
            continue
        if in_footer:
            _append_to_last(line)
            continue

        # Section header: a standalone line whose whitespace-normalised form
        # matches a known section name, and which we haven't already seen
        # (prevents false positives like "判決如\n主文" at the end of a judgment).
        normalized = _normalize_ws(line)
        if normalized in _SECTION_NAMES and normalized not in seen_sections:
            section = normalized
            seen_sections.add(section)
            current_l2_id = None
            current_l3_id = None
            _emit({"id": section, "section": section, "level": 1,
                   "heading": None, "text": ""})
            continue

        if section is None:
            # Haven't hit a section yet — skip header/meta noise.
            continue

        # Level 2: 一、xxx
        m2 = _RE_LEVEL2.match(line)
        if m2:
            num, rest = m2.group(1), m2.group(2).strip()
            current_l2_id = f"{section}.{num}"
            current_l3_id = None
            heading = rest if rest else None
            _emit({"id": current_l2_id, "section": section, "level": 2,
                   "heading": heading, "text": ""})
            continue

        # Level 3a: (一) xxx  /  （一） xxx
        m3p = _RE_LEVEL3_PAREN.match(line)
        if m3p and current_l2_id:
            num, rest = m3p.group(1), m3p.group(2).strip()
            current_l3_id = f"{current_l2_id}.({num})"
            heading = rest if rest else None
            _emit({"id": current_l3_id, "section": section, "level": 3,
                   "heading": heading, "text": ""})
            continue

        # Level 3b: ㈠㈡… (circled CJK numbers)
        m3c = _RE_LEVEL3_CIRCLED.match(line)
        if m3c and current_l2_id:
            circled, rest = m3c.group(1), m3c.group(2).strip()
            hanzi = _CIRCLED_TO_HANZI[circled]
            current_l3_id = f"{current_l2_id}.({hanzi})"
            heading = rest if rest else None
            _emit({"id": current_l3_id, "section": section, "level": 3,
                   "heading": heading, "text": ""})
            continue

        # Level 4: 1. xxx
        m4 = _RE_LEVEL4.match(line)
        if m4 and (current_l3_id or current_l2_id):
            parent = current_l3_id or current_l2_id
            num, rest = m4.group(1), m4.group(2).strip()
            _emit({"id": f"{parent}.{num}", "section": section, "level": 4,
                   "heading": None, "text": rest})
            continue

        # Plain continuation line — merge into the last paragraph's text.
        _append_to_last(line)

    # Fallback: nothing structural found at all.
    if not paragraphs:
        return [{"id": "全文", "section": "全文", "level": 1,
                 "heading": None, "text": " ".join(lines)}]

    return paragraphs


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
