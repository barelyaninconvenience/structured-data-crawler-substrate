"""Jobicy — public REST API source. Top-33 boards Phase 1, Tier A."""

from __future__ import annotations

import time
from typing import Iterator

import httpx

from ..normalize import NormalizedJob, make_normalized_job

API_URL = "https://jobicy.com/api/v2/remote-jobs"
SOURCE_NAME = "jobicy"


def fetch_all(
    limit: int | None = None,
    count: int = 50,
    geo: str | None = None,
    industry: str | None = None,
) -> Iterator[NormalizedJob]:
    """Fetch recent jobs from Jobicy public REST API.

    Args:
        limit: max jobs to yield (after API-side filtering)
        count: API-side page size (max 50 per request)
        geo: optional region filter (e.g. 'usa', 'europe')
        industry: optional industry filter
    """
    headers = {"User-Agent": "job-crawler/1.0 (personal research)"}
    params: dict[str, str | int] = {"count": min(count, 50)}
    if geo:
        params["geo"] = geo
    if industry:
        params["industry"] = industry

    with httpx.Client(timeout=30, headers=headers) as client:
        r = client.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()

    jobs = data.get("jobs", [])
    yielded = 0
    for item in jobs:
        title = item.get("jobTitle", "")
        company = item.get("companyName", "")
        url_field = item.get("url", "")
        if not title or not url_field:
            continue

        # Pay: Jobicy provides annualSalaryMin/Max + salaryCurrency
        smin = item.get("annualSalaryMin")
        smax = item.get("annualSalaryMax")
        scurrency = item.get("salaryCurrency", "")
        pay_raw = ""
        if smin or smax:
            pay_raw = f"{scurrency}{smin or ''}-{scurrency}{smax or ''} per year".strip("-")

        description = item.get("jobDescription", "")[:8000]
        posted = item.get("pubDate", "")
        job_type = item.get("jobType", "")
        if isinstance(job_type, list):
            job_type = ", ".join(job_type)
        job_geo = item.get("jobGeo", "")
        if isinstance(job_geo, list):
            job_geo = ", ".join(job_geo)
        job_industry = item.get("jobIndustry", "")
        if isinstance(job_industry, list):
            job_industry = ", ".join(job_industry)

        description_md = (
            f"{description}\n\n"
            f"Job type: {job_type}\n"
            f"Geo: {job_geo}\n"
            f"Industry: {job_industry}"
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
        # Jobicy is remote-only by definition
        if job.remote_status == "unclear":
            job.remote_status = "fully_remote"
        yield job
        yielded += 1
        if limit and yielded >= limit:
            break
        time.sleep(0.05)
