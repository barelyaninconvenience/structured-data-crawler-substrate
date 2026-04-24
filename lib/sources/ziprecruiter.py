"""ZipRecruiter public search via crawl4ai or direct HTTP.

ZipRecruiter exposes many job listings without login. Pagination via `page=N`.
"""

from __future__ import annotations

import urllib.parse as up

from ..normalize import NormalizedJob, make_normalized_job


def build_search_url(
    *, keywords: str = "remote", location: str = "Anywhere", page: int = 1,
) -> str:
    params = {
        "search": keywords,
        "location": location,
        "refine_by_location_type": "only_remote",
        "page": page,
    }
    return f"https://www.ziprecruiter.com/candidate/search?{up.urlencode(params)}"


def parse_html_extracted(
    *, source_url: str, extracted_markdown: str,
) -> NormalizedJob:
    """Parse ZipRecruiter job page markdown into NormalizedJob.

    Called by the crawl4ai or Chrome-MCP driver with extracted content.
    """
    lines = [l.strip() for l in extracted_markdown.splitlines() if l.strip()]
    title = ""
    company = ""
    pay_raw = ""

    for i, l in enumerate(lines[:30]):
        if l.startswith("# ") and not title:
            title = l.lstrip("# ").strip()
        # ZipRecruiter often has "At COMPANY" or "Company: COMPANY" near the top
        if not company and i < 15 and (" at " in l.lower() or l.lower().startswith("company")):
            if ":" in l:
                company = l.split(":", 1)[1].strip()
            elif " at " in l.lower():
                parts = l.split(" at ", 1)
                if len(parts) == 2 and len(parts[1]) < 80:
                    company = parts[1].strip()
        if ("$" in l or "/hr" in l or "per year" in l.lower()) and not pay_raw:
            pay_raw = l[:200]

    return make_normalized_job(
        source="ziprecruiter",
        source_url=source_url,
        title=title,
        company=company,
        pay_raw=pay_raw,
        description_md=extracted_markdown,
    )
