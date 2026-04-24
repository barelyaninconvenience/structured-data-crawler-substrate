"""Generic crawl4ai wrapper for public job pages.

Usage:
    async with AsyncWebCrawler() as crawler:
        async for job in crawl_jobs(crawler, urls, source='builtin'):
            ...
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from ..normalize import NormalizedJob, make_normalized_job

try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False


async def crawl_jobs(
    urls: list[str], source: str, delay_s: float = 1.0,
) -> AsyncIterator[NormalizedJob]:
    """Crawl a list of URLs and yield NormalizedJob objects.

    The extraction is markdown-based, so field parsing is heuristic. For
    structured extraction, use crawl4ai's JsonCssExtractionStrategy with
    site-specific selectors.
    """
    if not HAS_CRAWL4AI:
        raise RuntimeError("crawl4ai not installed. pip install crawl4ai")

    async with AsyncWebCrawler(verbose=False) as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url, bypass_cache=False)
            except Exception as e:
                print(f"[crawl4ai] error on {url}: {e}")
                continue

            markdown = result.markdown if hasattr(result, "markdown") else str(result)
            # Basic field extraction from markdown
            title, company, pay_raw = _extract_job_fields(markdown)
            if not title:
                continue
            yield make_normalized_job(
                source=source,
                source_url=url,
                title=title,
                company=company,
                pay_raw=pay_raw,
                description_md=markdown,
            )
            await asyncio.sleep(delay_s)


def _extract_job_fields(markdown: str) -> tuple[str, str, str]:
    """Best-effort extraction of (title, company, pay) from markdown."""
    import re
    lines = [l.strip() for l in markdown.splitlines() if l.strip()]
    title = ""
    company = ""
    pay_raw = ""

    for l in lines[:30]:
        if l.startswith("# "):
            title = l.lstrip("# ").strip()
            break
    if not title and lines:
        title = lines[0][:200]

    for l in lines[:30]:
        low = l.lower()
        if (low.startswith("at ") and len(l) < 80) or ("company:" in low):
            company = l.split(":", 1)[-1].strip().lstrip("at ").strip()
            break

    pay_re = re.compile(r"(\$[\d,]+(?:\s*[-–—]\s*\$?[\d,]+)?\s*(?:k|/\s*hr|/\s*year)?)", re.IGNORECASE)
    for l in lines[:60]:
        m = pay_re.search(l)
        if m:
            pay_raw = m.group(1)
            break

    return title, company, pay_raw
