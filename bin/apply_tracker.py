#!/usr/bin/env python3
"""Track application status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.apply_tracker import set_status, pipeline_report, VALID_STATUSES
from lib.storage import connect, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", help="Update application status for a job")
    p_set.add_argument("--job-id", required=True)
    p_set.add_argument("--status", choices=VALID_STATUSES, required=True)
    p_set.add_argument("--note", default="")

    p_report = sub.add_parser("report", help="Show pipeline report")

    args = ap.parse_args()

    conn = connect(DEFAULT_DB)
    if args.cmd == "set":
        set_status(conn, args.job_id, args.status, args.note)
        print(f"set {args.job_id} → {args.status}")
    elif args.cmd == "report":
        rows = pipeline_report(conn)
        if not rows:
            print("no applications tracked yet")
        else:
            current_status = None
            for r in rows:
                if r["status"] != current_status:
                    current_status = r["status"]
                    print(f"\n=== {current_status.upper()} ===")
                print(f"  [{r['job_id']}] {r['title']} @ {r['company']} — {r['pay_raw']}")
                if r["notes"]:
                    print(f"    notes: {r['notes'][:200]}")
    conn.close()


if __name__ == "__main__":
    main()
