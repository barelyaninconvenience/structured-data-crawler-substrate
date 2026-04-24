"""SkipTheDrive — public RSS feed. Top-33 boards Phase 1, Tier A."""

from __future__ import annotations

from typing import Iterator

from ..normalize import NormalizedJob, make_normalized_job

# SkipTheDrive exposes per-category RSS feeds; main aggregate feed:
DEFAULT_FEEDS = [
    "https://www.skipthedrive.com/feed/",
    "https://www.skipthedrive.com/category/remote-jobs/development/feed/",
    "https://www.skipthedrive.com/category/remote-jobs/customer-service/feed/",
    "https://www.skipthedrive.com/category/remote-jobs/sales/feed/",
    "https://www.skipthedrive.com/category/remote-jobs/marketing/feed/",
]
SOURCE_NAME = "skipthedrive"


def fetch_all(
    feed_urls: list[str] | None = None,
    limit: int | None = None,
) -> Iterator[NormalizedJob]:
    """Fetch recent jobs from SkipTheDrive per-category RSS feeds.

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
            # SkipTheDrive title is just the job title; company embedded in description
            title = entry.get("title", "").strip()
            description = entry.get("summary", "")
            link = entry.get("link", "")
            posted = entry.get("published", "")

            # Try to extract company from description (heuristic — first <strong> or first 'at X')
            company = ""
            import re
            m = re.search(r"(?:Company|Employer)\s*[:\-]?\s*([^\n<]+)", description, re.IGNORECASE)
            if m:
                company = m.group(1).strip()[:80]

            if not title or not link:
                continue

            job = make_normalized_job(
                source=SOURCE_NAME,
                source_url=link,
                title=title,
                company=company,
                description_md=description[:8000],
                posted_date=posted,
            )
            # SkipTheDrive is a remote-only board
            if job.remote_status == "unclear":
                job.remote_status = "fully_remote"
            yield job
            count += 1
            if limit and count >= limit:
                return
