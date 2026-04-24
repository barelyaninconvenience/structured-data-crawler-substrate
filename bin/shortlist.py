#!/usr/bin/env python3
"""Export a CSV shortlist of high-scoring jobs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.storage import connect, shortlist, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=int, default=9)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    conn = connect(DEFAULT_DB)
    rows = shortlist(conn, min_score=args.min_score)

    if not args.out:
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        args.out = DEFAULT_DB.parent / f"shortlist_{stamp}.csv"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        if not rows:
            print(f"no jobs >= {args.min_score}")
            return
        fieldnames = [
            "score_total", "recommend", "source", "title", "company",
            "pay_raw", "pay_min", "remote_status", "verdict",
            "red_flags", "green_flags", "application_status", "id",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                k: (json.loads(r[k]) if k in ("red_flags", "green_flags") and r[k] else r[k])
                for k in fieldnames
            })
    print(f"wrote {len(rows)} jobs → {args.out}")
    conn.close()


if __name__ == "__main__":
    main()
