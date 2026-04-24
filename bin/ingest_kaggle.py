#!/usr/bin/env python3
"""Ingest a Kaggle job-postings dataset into the pipeline DB.

Requires:
    - `pip install kaggle` (already done if you used requirements.txt)
    - Kaggle API creds at ~/.kaggle/kaggle.json (https://www.kaggle.com/settings → Create API Token)

Usage:
    python bin/ingest_kaggle.py --dataset jessysisca/job-descriptions-and-remote-task-descriptions
    python bin/ingest_kaggle.py --dataset DATASET --limit 100 --column-map '{"title":"JobTitle","company":"Company"}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.sources.kaggle_dataset import download_and_ingest
from lib.storage import connect, insert_job, backup_raw, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True,
                    help="Kaggle dataset slug (owner/dataset-name)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--column-map", type=str, default=None,
                    help="JSON dict mapping NormalizedJob fields to dataset column names")
    ap.add_argument("--init-db", action="store_true")
    args = ap.parse_args()

    if args.init_db:
        from lib.storage import init_db
        init_db()
        print("DB initialized")

    column_map = None
    if args.column_map:
        column_map = json.loads(args.column_map)

    conn = connect(DEFAULT_DB)
    # Ensure the kaggle source exists in the sources table
    conn.execute(
        """INSERT OR IGNORE INTO sources (source_id, display_name, auth_required, crawler_type, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (f"kaggle:{args.dataset}",
         f"Kaggle: {args.dataset}",
         1, "api",
         f"Imported from Kaggle dataset {args.dataset}"),
    )
    conn.commit()

    raw_dir = DEFAULT_DB.parent / "raw" / "kaggle"
    raw_dir.mkdir(parents=True, exist_ok=True)

    inserted = 0
    skipped = 0
    for job in download_and_ingest(args.dataset, column_map=column_map, limit=args.limit):
        job.raw_html_path = backup_raw(raw_dir, job.id, job.description_md)
        if insert_job(conn, job):
            inserted += 1
        else:
            skipped += 1
        if (inserted + skipped) % 100 == 0:
            print(f"  progress: inserted={inserted} skipped={skipped}")

    conn.close()
    print(f"\nKaggle ingest complete: inserted={inserted} skipped={skipped}")
    print("Next: python bin/dry_score.py && python bin/score.py && python bin/shortlist.py")


if __name__ == "__main__":
    main()
