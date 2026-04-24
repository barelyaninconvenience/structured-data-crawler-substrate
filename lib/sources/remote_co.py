"""Remote.co — public RSS feed (per category). Top-33 boards Phase 1, Tier A."""

from __future__ import annotations

import time
from typing import Iterator

from ..normalize import NormalizedJob, make_normalized_job

# Remote.co exposes per-category RSS feeds. Common useful categories:
DEFAULT_FEEDS = [
    "https://remote.co/remote-jobs/feed/",                        # all jobs
    "https://remote.co/remote-jobs/developer/feed/",
    "https://remote.co/remote-jobs/writing/feed/",
    "https://remote.co/remote-jobs/marketing/feed/",
    "https://remote.co/remote-jobs/customer-service/feed/",
    "https://remote.co/remote-jobs/design/feed/",
    "https://remote.co/remote-jobs/product/feed/",
]
SOURCE_NAME = "remote_co"


def fetch_all(
    feed_urls: list[str] | None = None,
    limit: int | None = None,
) -> Iterator[NormalizedJob]:
    """Fetch recent jobs from Remote.co per-category RSS feeds.

    Args:
        feed_urls: list of feed URLs; defaults to DEFAULT_FEEDS
        limit: max jobs to yield TOTAL across all feeds
    """
    import feedparser

    feeds = feed_urls or DEFAULT_FEEDS
    count = 0
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            # Remote.co title format varies; commonly "Job Title - Company"
            raw_title = entry.get("title", "")
            if " - " in raw_title:
                # Try "Title - Company" split (heuristic)
                parts = raw_title.rsplit(" - ", 1)
                if len(parts) == 2 and len(parts[1]) < 80:
                    title, company = parts
                else:
                    title = raw_title
                    company = ""
            else:
                title = raw_title
                company = ""

            yield make_normalized_job(
                source=SOURCE_NAME,
                source_url=entry.get("link", ""),
                title=title.strip(),
                company=company.strip(),
                description_md=entry.get("summary", ""),
                posted_date=entry.get("published", ""),
            )
            count += 1
            if limit and count >= limit:
                return
        time.sleep(0.1)  # polite between feeds
