#!/usr/bin/env python3
"""Score unscored jobs against the rubric."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.score import score_job
from lib.storage import connect, unscored_jobs, save_score, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--limit", type=int, default=None,
                    help="max jobs to score in this run")
    ap.add_argument("--unscored", action="store_true", default=True)
    ap.add_argument("--delay", type=float, default=0.5,
                    help="seconds between API calls")
    args = ap.parse_args()

    conn = connect(DEFAULT_DB)
    jobs = unscored_jobs(conn, limit=args.limit)
    print(f"found {len(jobs)} unscored jobs")

    for i, row in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] scoring {row['id']}: {row['title'][:60]}")
        try:
            result = score_job(
                title=row["title"],
                company=row["company"] or "",
                pay=row["pay_raw"] or "",
                remote=row["remote_status"] or "unclear",
                description=(row["description_md"] or "")[:4000],
                model=args.model,
            )
            save_score(conn, row["id"], result, model_used=args.model)
            total = sum(
                result.get(k, 0) for k in (
                    "score_automatability", "score_oversight", "score_pay",
                    "score_remote", "score_stakes", "score_flexibility",
                )
            )
            print(f"   → {total}/12 [{result.get('recommend', '?')}] {result.get('verdict', '')[:80]}")
        except Exception as e:
            print(f"   ! error: {e}")
        time.sleep(args.delay)

    conn.close()


if __name__ == "__main__":
    main()
