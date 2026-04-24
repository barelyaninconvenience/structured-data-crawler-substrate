"""Remotive — public REST API source. Top-33 boards Phase 1, Tier A."""

from __future__ import annotations

import time
from typing import Iterator

import httpx

from ..normalize import NormalizedJob, make_normalized_job

API_URL = "https://remotive.com/api/remote-jobs"
SOURCE_NAME = "remotive"


def fetch_all(limit: int | None = None, category: str | None = None) -> Iterator[NormalizedJob]:
    """Fetch recent jobs from Remotive's public REST API.

    The API returns a JSON object with 'jobs' array. Each entry has structured
    fields (job_type, salary, candidate_required_location, description, etc.).

    Args:
        limit: max jobs to yield
        category: optional filter (e.g. 'software-dev', 'data', 'devops')
    """
    headers = {"User-Agent": "job-crawler/1.0 (personal research)"}
    url = API_URL
    if category:
        url = f"{API_URL}?category={category}"

    with httpx.Client(timeout=30, headers=headers) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()

    jobs = data.get("jobs", [])
    count = 0
    for item in jobs:
        title = item.get("title", "")
        company = item.get("company_name", "")
        url_field = item.get("url", "")
        if not title or not url_field:
            continue

        # Pay: Remotive provides 'salary' as a free-text string
        pay_raw = item.get("salary", "")

        # Description: strip HTML for cleaner LLM scoring; keep first 8K chars
        description = item.get("description", "")[:8000]

        # Posted date in 'publication_date' as ISO 8601
        posted = item.get("publication_date", "")

        # Tags / job_type contribute to remote-status determination
        tags = " ".join(item.get("tags", []))
        job_type = item.get("job_type", "")
        candidate_loc = item.get("candidate_required_location", "")

        description_md = (
            f"{description}\n\n"
            f"Tags: {tags}\n"
            f"Job type: {job_type}\n"
            f"Candidate required location: {candidate_loc}"
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
        # Remotive is a remote-only board — promote 'unclear' to 'fully_remote'
        if job.remote_status == "unclear":
            job.remote_status = "fully_remote"
        yield job
        count += 1
        if limit and count >= limit:
            break
        time.sleep(0.05)  # polite
