"""Web scraper connector with anti-block headers, parsing, and rate limiting."""

import time
import random

import requests
from bs4 import BeautifulSoup


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


class ScraperError(Exception):
    """Custom exception for scraping errors."""

    def __init__(self, status_code: int, message: str, url: str = ""):
        self.status_code = status_code
        self.message = message
        self.url = url
        super().__init__(f"[{status_code}] {url}: {message}")


def _get_headers() -> dict:
    """Get request headers with a random User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def fetch_page(
    url: str,
    params: dict | None = None,
    retries: int = 3,
    timeout: int = 30,
) -> BeautifulSoup:
    """Fetch a web page and return parsed BeautifulSoup object.

    Args:
        url: Page URL to fetch.
        params: Query parameters.
        retries: Number of retry attempts.
        timeout: Request timeout in seconds.

    Returns:
        Parsed BeautifulSoup object.

    Raises:
        ScraperError: On HTTP errors or after all retries exhausted.
    """
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                params=params,
                headers=_get_headers(),
                timeout=timeout,
            )

            if response.status_code >= 400:
                raise ScraperError(
                    status_code=response.status_code,
                    message=response.text[:500],
                    url=url,
                )

            response.encoding = response.apparent_encoding
            return BeautifulSoup(response.text, "html.parser")

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                wait = 2**attempt + random.uniform(0.5, 1.5)
                time.sleep(wait)
            else:
                raise ScraperError(
                    status_code=0,
                    message="Request failed after all retries",
                    url=url,
                )


def fetch_json(
    url: str,
    params: dict | None = None,
    retries: int = 3,
    timeout: int = 30,
) -> dict:
    """Fetch a URL expecting JSON response (for unofficial JSON APIs).

    Args:
        url: URL to fetch.
        params: Query parameters.
        retries: Number of retry attempts.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON as dict.
    """
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                params=params,
                headers=_get_headers(),
                timeout=timeout,
            )

            if response.status_code >= 400:
                raise ScraperError(
                    status_code=response.status_code,
                    message=response.text[:500],
                    url=url,
                )

            return response.json()

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                wait = 2**attempt + random.uniform(0.5, 1.5)
                time.sleep(wait)
            else:
                raise ScraperError(
                    status_code=0,
                    message="Request failed after all retries",
                    url=url,
                )


def scrape_list(
    base_url: str,
    page_param: str = "page",
    start_page: int = 1,
    max_pages: int = 10,
    item_selector: str = "",
    parse_item_fn=None,
    rate_limit_delay: float = 1.0,
) -> list[dict]:
    """Scrape a paginated list of items.

    Args:
        base_url: Base URL (page param will be appended).
        page_param: Query parameter name for page number.
        start_page: First page number.
        max_pages: Maximum pages to scrape.
        item_selector: CSS selector for individual items on the page.
        parse_item_fn: Function(BeautifulSoup element) -> dict to parse each item.
        rate_limit_delay: Seconds between page requests.

    Returns:
        List of parsed item dicts.
    """
    all_items = []

    for page in range(start_page, start_page + max_pages):
        soup = fetch_page(base_url, params={page_param: page})

        if not item_selector or not parse_item_fn:
            break

        elements = soup.select(item_selector)
        if not elements:
            break

        for el in elements:
            item = parse_item_fn(el)
            if item:
                all_items.append(item)

        if page < start_page + max_pages - 1:
            time.sleep(rate_limit_delay)

    return all_items
