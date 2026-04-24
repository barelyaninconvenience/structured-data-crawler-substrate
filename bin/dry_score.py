#!/usr/bin/env python3
"""Pre-score jobs using free heuristics (no LLM). Saves API cost."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.dry_score import dry_score
from lib.storage import connect, unscored_jobs, save_score, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--threshold", type=int, default=7,
                    help="Below this heuristic score, mark as 'skip' (default: 7)")
    args = ap.parse_args()

    conn = connect(DEFAULT_DB)
    jobs = unscored_jobs(conn, limit=args.limit)
    print(f"dry-scoring {len(jobs)} jobs")

    skipped = 0
    flagged = 0
    for row in jobs:
        result = dry_score(
            title=row["title"],
            description=(row["description_md"] or "")[:4000],
            pay_raw=row["pay_raw"] or "",
            remote_status=row["remote_status"] or "unclear",
            pay_min=row["pay_min"],
            pay_type=row["pay_type"] or "unknown",
        )
        if result["score_total"] < args.threshold:
            save_score(conn, row["id"], result, model_used="heuristic")
            skipped += 1
        else:
            flagged += 1

    print(f"skipped (saved as heuristic-scored): {skipped}")
    print(f"flagged for LLM scoring: {flagged}")
    conn.close()


if __name__ == "__main__":
    main()
