"""RSS/Atom feed connector with parsing and date normalization."""

import time
from datetime import datetime

import feedparser


class FeedError(Exception):
    """Custom exception for feed errors."""

    def __init__(self, message: str, feed_url: str = ""):
        self.message = message
        self.feed_url = feed_url
        super().__init__(f"{feed_url}: {message}")


def fetch_feed(
    feed_url: str,
    retries: int = 3,
    timeout: int = 30,
) -> feedparser.FeedParserDict:
    """Fetch and parse an RSS/Atom feed.

    Args:
        feed_url: URL of the RSS/Atom feed.
        retries: Number of retry attempts.
        timeout: Request timeout in seconds.

    Returns:
        Parsed feed object.

    Raises:
        FeedError: If feed cannot be fetched or parsed.
    """
    for attempt in range(retries):
        try:
            feed = feedparser.parse(feed_url, request_headers={
                "User-Agent": "MCP-Server/1.0 (RSS Reader)",
            })

            if feed.bozo and not feed.entries:
                raise FeedError(
                    message=f"Feed parsing error: {feed.bozo_exception}",
                    feed_url=feed_url,
                )

            return feed

        except Exception as e:
            if isinstance(e, FeedError):
                raise
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                raise FeedError(
                    message=f"Failed after {retries} attempts: {e}",
                    feed_url=feed_url,
                )


def get_entries(
    feed_url: str,
    max_entries: int = 50,
    since: str | None = None,
) -> list[dict]:
    """Fetch feed entries with optional date filtering.

    Args:
        feed_url: URL of the RSS/Atom feed.
        max_entries: Maximum number of entries to return.
        since: Only return entries after this date (ISO format YYYY-MM-DD).

    Returns:
        List of normalized entry dicts.
    """
    feed = fetch_feed(feed_url)
    entries = []

    since_dt = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d")

    for entry in feed.entries[:max_entries]:
        parsed = normalize_entry(entry)

        if since_dt and parsed.get("published_dt"):
            if parsed["published_dt"] < since_dt:
                continue

        entries.append(parsed)

    return entries


def normalize_entry(entry) -> dict:
    """Normalize a feed entry into a consistent dict format.

    Args:
        entry: A feedparser entry object.

    Returns:
        Dict with standardized keys.
    """
    published_dt = None
    published_str = ""

    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published_dt = datetime(*entry.published_parsed[:6])
        published_str = published_dt.strftime("%Y-%m-%d %H:%M:%S")
    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
        published_dt = datetime(*entry.updated_parsed[:6])
        published_str = published_dt.strftime("%Y-%m-%d %H:%M:%S")

    summary = ""
    if hasattr(entry, "summary"):
        summary = entry.summary
    elif hasattr(entry, "description"):
        summary = entry.description

    return {
        "title": getattr(entry, "title", ""),
        "link": getattr(entry, "link", ""),
        "published": published_str,
        "published_dt": published_dt,
        "summary": summary,
        "author": getattr(entry, "author", ""),
        "tags": [tag.term for tag in getattr(entry, "tags", [])],
    }


def fetch_multiple_feeds(
    feed_urls: list[str],
    max_entries_per_feed: int = 20,
    rate_limit_delay: float = 0.5,
) -> list[dict]:
    """Fetch entries from multiple feeds, sorted by date.

    Args:
        feed_urls: List of feed URLs.
        max_entries_per_feed: Max entries per feed.
        rate_limit_delay: Delay between feed requests.

    Returns:
        Combined list of entries sorted by published date (newest first).
    """
    all_entries = []

    for i, url in enumerate(feed_urls):
        try:
            entries = get_entries(url, max_entries=max_entries_per_feed)
            for entry in entries:
                entry["source_url"] = url
            all_entries.extend(entries)
        except FeedError:
            continue

        if i < len(feed_urls) - 1:
            time.sleep(rate_limit_delay)

    all_entries.sort(
        key=lambda e: e.get("published_dt") or datetime.min,
        reverse=True,
    )

    return all_entries
