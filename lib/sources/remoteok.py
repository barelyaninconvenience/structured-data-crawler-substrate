"""RemoteOK public API source."""

from __future__ import annotations

import time
from typing import Iterator

import httpx

from ..normalize import NormalizedJob, make_normalized_job

API_URL = "https://remoteok.com/api"


def fetch_all(limit: int | None = None) -> Iterator[NormalizedJob]:
    """Fetch recent jobs from RemoteOK. The API returns an array of jobs;
    the first element is a legal/info object that we skip."""
    headers = {"User-Agent": "job-crawler/1.0 (personal research)"}
    with httpx.Client(timeout=30, headers=headers) as client:
        r = client.get(API_URL)
        r.raise_for_status()
        data = r.json()

    count = 0
    for item in data:
        if "legal" in item or "id" not in item:
            continue
        url = item.get("url") or item.get("apply_url") or ""
        title = item.get("position") or item.get("title") or ""
        company = item.get("company") or ""
        pay_raw = ""
        if item.get("salary_min") or item.get("salary_max"):
            smin = item.get("salary_min", "")
            smax = item.get("salary_max", "")
            pay_raw = f"${smin}-${smax}".replace("$-", "").strip()
        description = item.get("description", "")
        posted = item.get("date", "")
        tags = " ".join(item.get("tags", []))
        # RemoteOK jobs are remote by definition, but confirm in text
        description_md = f"{description}\n\nTags: {tags}"

        job = make_normalized_job(
            source="remoteok",
            source_url=url,
            title=title,
            company=company,
            pay_raw=pay_raw,
            description_md=description_md,
            posted_date=posted,
        )
        # RemoteOK is a remote-only board by definition
        if job.remote_status == "unclear":
            job.remote_status = "fully_remote"
        yield job
        count += 1
        if limit and count >= limit:
            break
        time.sleep(0.05)  # polite
