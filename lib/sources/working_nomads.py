"""Working Nomads — public RSS / JSON feed. Top-33 boards Phase 1, Tier A."""

from __future__ import annotations

import time
from typing import Iterator

import httpx

from ..normalize import NormalizedJob, make_normalized_job

# Working Nomads exposes a JSON feed at this endpoint (per their documentation).
# Falls back to RSS if JSON unavailable.
JSON_URL = "https://www.workingnomads.com/api/exposed_jobs/"
RSS_URL  = "https://www.workingnomads.com/jobsrss"
SOURCE_NAME = "working_nomads"


def fetch_all(limit: int | None = None) -> Iterator[NormalizedJob]:
    """Fetch recent jobs from Working Nomads.

    Tries JSON endpoint first; falls back to RSS via feedparser if JSON fails.
    """
    headers = {"User-Agent": "job-crawler/1.0 (personal research)"}

    # Try JSON
    try:
        with httpx.Client(timeout=30, headers=headers) as client:
            r = client.get(JSON_URL)
            r.raise_for_status()
            data = r.json()
        yield from _from_json(data, limit)
        return
    except Exception:
        pass  # Fall through to RSS

    # RSS fallback
    yield from _from_rss(limit)


def _from_json(data: list[dict] | dict, limit: int | None) -> Iterator[NormalizedJob]:
    """Yield from JSON payload. Endpoint typically returns a list of job dicts."""
    if isinstance(data, dict):
        items = data.get("jobs", data.get("results", []))
    else:
        items = data

    count = 0
    for item in items:
        title = item.get("title", "")
        company = item.get("company_name", item.get("company", ""))
        url_field = item.get("url", "")
        if not title or not url_field:
            continue

        pay_raw = item.get("salary", "")
        description = item.get("description", "")[:8000]
        posted = item.get("pub_date", item.get("published", ""))
        category = item.get("category_name", item.get("category", ""))
        location = item.get("location", "")

        description_md = (
            f"{description}\n\n"
            f"Category: {category}\n"
            f"Location: {location}"
        )

        job = make_normalized_job(
            source=SOURCE_NAME,
            source_url=url_field,
            title=title,
            company=company,
            pay_raw=pay_raw,
            description_md=description_md,
            posted_date=posted,
        )
        if job.remote_status == "unclear":
            job.remote_status = "fully_remote"
        yield job
        count += 1
        if limit and count >= limit:
            break
        time.sleep(0.05)


def _from_rss(limit: int | None) -> Iterator[NormalizedJob]:
    """Yield from RSS feed (fallback)."""
    import feedparser
    parsed = feedparser.parse(RSS_URL)
    count = 0
    for entry in parsed.entries:
        # Working Nomads RSS title format: "Job Title at Company"
        raw_title = entry.get("title", "")
        if " at " in raw_title:
            title, company = raw_title.split(" at ", 1)
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
            break
