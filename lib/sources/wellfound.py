"""Wellfound (formerly AngelList Talent) via Chrome MCP.

Wellfound requires login for most job details. Driven by Chrome MCP.
Rule: ~6 seconds between requests.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..normalize import NormalizedJob, make_normalized_job


def build_search_url(
    *, role: str = "", remote_only: bool = True,
) -> str:
    import urllib.parse as up
    base = "https://wellfound.com/jobs"
    params = {}
    if role:
        params["role"] = role
    if remote_only:
        params["remote"] = "true"
    if params:
        return f"{base}?{up.urlencode(params)}"
    return base


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
        elif not company and i < 12 and len(l) < 80:
            if "at " in l.lower() and not l.startswith("#"):
                # Wellfound pattern: "Role at Company"
                if " at " in l.lower():
                    parts = l.split(" at ", 1)
                    if len(parts) == 2:
                        if not title:
                            title = parts[0].strip()
                        company = parts[1].strip()
                        break
        if "$" in l and not pay_raw:
            pay_raw = l[:200]

    return make_normalized_job(
        source="wellfound",
        source_url=source_url,
        title=title,
        company=company,
        pay_raw=pay_raw,
        description_md=extracted_markdown,
    )
