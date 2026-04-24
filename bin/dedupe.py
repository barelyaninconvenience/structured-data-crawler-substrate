#!/usr/bin/env python3
"""Run deduplication across the corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.dedupe_run import run_dedupe
from lib.storage import connect, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=85.0,
                    help="Fuzzy match threshold 0-100 (default: 85)")
    args = ap.parse_args()

    conn = connect(DEFAULT_DB)
    created = run_dedupe(conn, threshold=args.threshold)
    print(f"created {created} dedup groups")

    # Also report
    total_dedup = conn.execute(
        "SELECT COUNT(*) FROM raw_jobs WHERE dedup_group_id IS NOT NULL"
    ).fetchone()[0]
    print(f"total jobs in dedup groups: {total_dedup}")
    conn.close()


if __name__ == "__main__":
    main()
