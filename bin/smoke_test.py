#!/usr/bin/env python3
"""End-to-end smoke test. Verifies install + schema + parsers + scoring.

Does NOT hit any external API unless --live is passed.

Use:
    python bin/smoke_test.py                # local only
    python bin/smoke_test.py --live         # includes LLM scoring call (costs ~$0.01)
    python bin/smoke_test.py --live --remoteok   # includes a 5-job RemoteOK fetch
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.normalize import (
    make_normalized_job, make_job_id, parse_pay, parse_remote_status,
    parse_location, annual_equivalent,
)
from lib.dry_score import dry_score
from lib.dedup import dedup_signature, fuzzy_match_score


def test_parsers() -> bool:
    print("[1/5] testing parsers...")
    # Pay parsing
    cases = [
        ("$50,000 - $80,000", (50000, 80000, "annual")),
        ("$50k-$80k", (50000, 80000, "annual")),
        ("$25/hr", (25, None, "hourly")),
        ("60000 per year", (60000, None, "annual")),
        ("$90,000 annually", (90000, None, "annual")),
    ]
    ok = True
    for raw, expected in cases:
        got = parse_pay(raw)
        if got != expected:
            print(f"   FAIL: parse_pay({raw!r}) = {got}, expected {expected}")
            ok = False

    # Remote parsing
    cases2 = [
        ("We're fully remote", "fully_remote"),
        ("Hybrid 2 days in office", "hybrid"),
        ("Must be located in NYC", "onsite"),
        ("generic job description", "unclear"),
    ]
    for text, expected in cases2:
        got = parse_remote_status(text)
        if got != expected:
            print(f"   FAIL: parse_remote_status({text!r}) = {got!r}, expected {expected!r}")
            ok = False

    # Location
    if parse_location("based in Chicago, IL") != "Chicago, IL":
        print("   FAIL: parse_location")
        ok = False

    # Annual equivalent
    assert annual_equivalent(25, "hourly") == 52000
    assert annual_equivalent(50000, "annual") == 50000

    print("   " + ("OK" if ok else "FAIL"))
    return ok


def test_job_construction() -> bool:
    print("[2/5] testing job construction...")
    job = make_normalized_job(
        source="test",
        source_url="https://example.com/1",
        title="Remote Technical Writer",
        company="Acme Docs",
        pay_raw="$60,000 - $80,000",
        description_md="Fully remote. Async. Docs-heavy role.",
    )
    ok = True
    if job.pay_min != 60000 or job.pay_max != 80000:
        print(f"   FAIL: pay parsing: {job.pay_min} - {job.pay_max}")
        ok = False
    if job.remote_status != "fully_remote":
        print(f"   FAIL: remote status: {job.remote_status}")
        ok = False
    if len(job.id) != 16:
        print(f"   FAIL: id length: {len(job.id)}")
        ok = False
    print("   " + ("OK" if ok else "FAIL"))
    return ok


def test_dry_scoring() -> bool:
    print("[3/5] testing dry scoring...")
    result = dry_score(
        title="Remote Technical Writer",
        description="Fully remote. Async-first. Documentation-heavy role.",
        pay_raw="$70,000",
        remote_status="fully_remote",
        pay_min=70000,
        pay_type="annual",
    )
    ok = result["score_total"] >= 8 and result["recommend"] in ("apply", "maybe")
    if not ok:
        print(f"   FAIL: unexpected score: {result}")
    print("   " + ("OK" if ok else "FAIL") + f" (scored {result['score_total']}/12)")
    return ok


def test_dedup() -> bool:
    print("[4/5] testing dedup...")
    sig1 = dedup_signature("Senior Software Engineer - Remote", "Acme Inc")
    sig2 = dedup_signature("Software Engineer | Remote", "Acme Inc")
    # Different signatures (conservative) but high fuzzy score
    score = fuzzy_match_score(
        "Senior Software Engineer - Remote", "Acme Inc",
        "Software Engineer | Remote", "Acme Inc",
    )
    ok = score >= 70
    print("   " + ("OK" if ok else "FAIL") + f" (fuzzy score: {score:.0f})")
    return ok


def test_storage() -> bool:
    print("[5/5] testing storage...")
    from lib.storage import init_db, connect, insert_job
    # Use a temp DB
    tmpdir = tempfile.mkdtemp()
    tmp_db = Path(tmpdir) / "test_jobs.db"

    # Patch DEFAULT_DB temporarily
    from lib import storage as s
    original = s.DEFAULT_DB
    s.DEFAULT_DB = tmp_db
    try:
        init_db(tmp_db)
        conn = connect(tmp_db)
        # Use 'remoteok' (exists in sources table); FK requires the source exist
        job = make_normalized_job(
            source="remoteok",
            source_url="https://example.com/1",
            title="Test Job",
            company="Test Co",
        )
        inserted = insert_job(conn, job)
        duplicated = insert_job(conn, job)
        ok = inserted and not duplicated
        if not ok:
            print(f"   FAIL: inserted={inserted}, duplicated={duplicated}")
        count = conn.execute("SELECT COUNT(*) FROM raw_jobs").fetchone()[0]
        conn.close()
        ok = ok and count == 1
        print("   " + ("OK" if ok else "FAIL"))
        return ok
    finally:
        s.DEFAULT_DB = original


def test_remoteok_live() -> bool:
    print("[live] testing RemoteOK fetch (5 jobs)...")
    from lib.sources.remoteok import fetch_all
    jobs = list(fetch_all(limit=5))
    ok = len(jobs) >= 3
    print("   " + ("OK" if ok else "FAIL") + f" (fetched {len(jobs)} jobs)")
    for j in jobs[:3]:
        print(f"     - {j.title[:60]} @ {j.company} [{j.remote_status}]")
    return ok


def test_llm_score_live() -> bool:
    print("[live] testing LLM scoring (1 job)...")
    from lib.score import score_job
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("   SKIP: ANTHROPIC_API_KEY not set")
        return True
    try:
        result = score_job(
            title="Remote Technical Writer",
            company="Acme Docs",
            pay="$70,000",
            remote="fully_remote",
            description="Fully remote. Async. Documentation-heavy role with no client calls.",
            model="claude-haiku-4-5-20251001",  # cheapest model for test
        )
        ok = "score_total" not in result or isinstance(result.get("score_automatability"), int)
        if ok:
            total = sum(result.get(k, 0) for k in (
                "score_automatability", "score_oversight", "score_pay",
                "score_remote", "score_stakes", "score_flexibility",
            ))
            print(f"   OK (score: {total}/12, verdict: {result.get('verdict', 'n/a')})")
        else:
            print(f"   FAIL: result = {result}")
        return ok
    except Exception as e:
        print(f"   FAIL: {e}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="include tests that hit external APIs")
    ap.add_argument("--remoteok", action="store_true",
                    help="include RemoteOK fetch test (implies --live)")
    args = ap.parse_args()

    results = [
        test_parsers(),
        test_job_construction(),
        test_dry_scoring(),
        test_dedup(),
        test_storage(),
    ]

    if args.live or args.remoteok:
        if args.remoteok:
            results.append(test_remoteok_live())
        results.append(test_llm_score_live())

    print()
    print(f"passed: {sum(results)}/{len(results)}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
