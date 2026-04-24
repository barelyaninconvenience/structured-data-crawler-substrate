"""We Work Remotely — RSS feed parser (public, no auth)."""

from __future__ import annotations

from typing import Iterator

import feedparser

from ..normalize import NormalizedJob, make_normalized_job

# WWR exposes per-category RSS feeds. A few useful ones:
DEFAULT_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-copywriting-jobs.rss",
    "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
    "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
    "https://weworkremotely.com/categories/remote-product-jobs.rss",
    "https://weworkremotely.com/categories/remote-business-exec-management-jobs.rss",
    "https://weworkremotely.com/categories/all-other-remote-jobs.rss",
]


def fetch_all(
    feed_urls: list[str] | None = None, limit: int | None = None,
) -> Iterator[NormalizedJob]:
    feeds = feed_urls or DEFAULT_FEEDS
    count = 0
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            # WWR title format: "Company: Job Title"
            raw_title = entry.get("title", "")
            if ": " in raw_title:
                company, title = raw_title.split(": ", 1)
            else:
                company = ""
                title = raw_title

            yield make_normalized_job(
                source="wwr",
                source_url=entry.get("link", ""),
                title=title.strip(),
                company=company.strip(),
                description_md=entry.get("summary", ""),
                posted_date=entry.get("published", ""),
            )
            count += 1
            if limit and count >= limit:
                return
