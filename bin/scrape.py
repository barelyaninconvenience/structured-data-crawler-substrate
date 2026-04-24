#!/usr/bin/env python3
"""Scrape jobs from a source and insert into the DB."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.storage import connect, init_db, insert_job, backup_raw, DEFAULT_DB


def scrape_remoteok(limit: int | None) -> None:
    from lib.sources.remoteok import fetch_all
    conn = connect(DEFAULT_DB)
    inserted = 0
    skipped = 0
    raw_dir = DEFAULT_DB.parent / "raw" / "remoteok"
    for job in fetch_all(limit=limit):
        job.raw_html_path = backup_raw(raw_dir, job.id, job.description_md)
        if insert_job(conn, job):
            inserted += 1
        else:
            skipped += 1
    print(f"remoteok: inserted={inserted} skipped={skipped}")
    conn.close()


def scrape_handshake_plan(urls_path: Path) -> None:
    from lib.sources.handshake import load_urls, write_scraping_plan
    urls = load_urls(urls_path)
    plan_path = DEFAULT_DB.parent / "raw" / "handshake" / "plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    write_scraping_plan(urls, plan_path)
    print(f"handshake: {len(urls)} URLs → {plan_path}")
    print("Next: use Chrome MCP to execute each task in the plan; call")
    print("ingest_handshake_chrome(source_url, extracted_markdown) for each.")


def ingest_handshake_chrome(source_url: str, extracted_markdown: str) -> None:
    """Called by the Chrome-MCP-driving script (one job at a time) to ingest."""
    from lib.sources.handshake import parse_chrome_extracted
    conn = connect(DEFAULT_DB)
    job = parse_chrome_extracted(
        source_url=source_url, extracted_markdown=extracted_markdown,
    )
    raw_dir = DEFAULT_DB.parent / "raw" / "handshake"
    job.raw_html_path = backup_raw(raw_dir, job.id, job.description_md)
    if insert_job(conn, job):
        print(f"inserted {job.id}: {job.title} @ {job.company}")
    else:
        print(f"already present: {job.id}")
    conn.close()


async def scrape_crawl4ai(urls: list[str], source: str) -> None:
    from lib.sources.crawl4ai_generic import crawl_jobs
    conn = connect(DEFAULT_DB)
    inserted = 0
    raw_dir = DEFAULT_DB.parent / "raw" / source
    async for job in crawl_jobs(urls, source=source):
        job.raw_html_path = backup_raw(raw_dir, job.id, job.description_md)
        if insert_job(conn, job):
            inserted += 1
            print(f"  + {job.title} @ {job.company}")
    print(f"{source}: inserted={inserted}")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    choices=["remoteok", "handshake", "wwr", "builtin", "generic"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--urls", type=Path, default=None,
                    help="Path to file with URLs (for handshake/generic)")
    ap.add_argument("--init-db", action="store_true")
    args = ap.parse_args()

    if args.init_db:
        init_db()
        print("DB initialized")

    if args.source == "remoteok":
        scrape_remoteok(args.limit)
    elif args.source == "handshake":
        if not args.urls:
            ap.error("--urls required for handshake")
        scrape_handshake_plan(args.urls)
    elif args.source in ("builtin", "generic"):
        if not args.urls:
            ap.error("--urls required")
        with open(args.urls) as f:
            urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        asyncio.run(scrape_crawl4ai(urls, args.source))
    else:
        print(f"source {args.source} not yet implemented")


if __name__ == "__main__":
    main()
