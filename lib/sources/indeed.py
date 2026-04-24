"""Indeed via Chrome MCP.

Indeed has looser restrictions than LinkedIn but still detects scrapers.
Rule: ~5 seconds between requests, max 100 per session.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..normalize import NormalizedJob, make_normalized_job


def build_search_url(
    *, q: str = "remote", l: str = "", remotejob: bool = True,
    salary_min: int | None = None, page: int = 1,
) -> str:
    import urllib.parse as up
    params = {
        "q": q,
        "l": l,
        "start": (page - 1) * 10,
    }
    if remotejob:
        params["sc"] = "0kf%3Aattr%28DSQF7%29%3B"  # remote filter token
    if salary_min:
        params["salary"] = f"${salary_min:,}"
    return f"https://www.indeed.com/jobs?{up.urlencode(params)}"


def parse_chrome_extracted(
    *, source_url: str, extracted_markdown: str,
) -> NormalizedJob:
    lines = [l.strip() for l in extracted_markdown.splitlines() if l.strip()]
    title = ""
    company = ""
    pay_raw = ""

    for i, l in enumerate(lines[:40]):
        if l.startswith("# ") and not title:
            title = l.lstrip("# ").strip()
        elif not company and i < 15 and len(l) < 80 and "$" not in l:
            if not l.startswith("#") and "apply" not in l.lower():
                company = l
        if ("$" in l or "/hr" in l or "/year" in l) and not pay_raw:
            pay_raw = l[:200]

    return make_normalized_job(
        source="indeed",
        source_url=source_url,
        title=title,
        company=company,
        pay_raw=pay_raw,
        description_md=extracted_markdown,
    )


def write_scraping_plan(urls: list[str], out_path: Path) -> None:
    plan = {
        "source": "indeed",
        "task_count": len(urls),
        "rate_limit_seconds": 5,
        "max_per_session": 100,
        "tasks": [{"url": u, "timeout_ms": 30000} for u in urls],
    }
    out_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
