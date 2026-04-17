"""Pure HTML parser for 司法院裁判書用語辭典資料庫查詢系統.

All functions are stateless: they take an HTML string and return structured data.
No HTTP calls here — fetching is handled by connectors/rest_client.py.
"""

from bs4 import BeautifulSoup


def parse_term_definitions(html: str) -> dict:
    """Parse term definitions from a TermContent.aspx response.

    Page structure (inside div.fy_page_content):
      For each definition entry:
        div.fy_terms > div.term        — term name
        div.fy_term_jtname             — "適用之法領域：{domain}"
        div.fy_term_content            — explanation text
        hr
      div.memo                         — disclaimer at the bottom

    Args:
        html: Raw HTML of /TermContent.aspx response.

    Returns:
        Dict with keys:
        - term: the queried term name (from first entry, empty string if not found)
        - definitions: list of dicts with keys:
            - domain: applicable legal domain (e.g. "民事", "刑事")
            - explanation: full explanation text
        - disclaimer: footnote text (e.g. "本解釋內容僅供參考，不拘束個案")
    """
    soup = BeautifulSoup(html, "html.parser")

    term_name = ""
    definitions = []

    for term_div in soup.select("div.fy_terms"):
        name_tag = term_div.select_one("div.term")
        if name_tag and not term_name:
            term_name = name_tag.get_text(strip=True)

        domain_div = term_div.find_next_sibling("div", class_="fy_term_jtname")
        content_div = term_div.find_next_sibling("div", class_="fy_term_content")

        domain = ""
        if domain_div:
            raw = domain_div.get_text(strip=True)
            # "適用之法領域：民事" → "民事"
            domain = raw.split("：", 1)[-1].strip()

        explanation = content_div.get_text(" ", strip=True) if content_div else ""

        definitions.append({
            "domain":      domain,
            "explanation": explanation,
        })

    memo = soup.select_one("div.memo")
    disclaimer = memo.get_text(strip=True) if memo else ""

    return {
        "term":        term_name,
        "definitions": definitions,
        "disclaimer":  disclaimer,
    }
