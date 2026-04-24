#!/usr/bin/env python3
"""Run the full pipeline end-to-end across public sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.full_pipeline import run_pipeline
from lib.storage import init_db


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--remoteok-limit", type=int, default=100)
    ap.add_argument("--wwr-limit", type=int, default=100)
    ap.add_argument("--llm-threshold", type=int, default=7,
                    help="Heuristic score below which jobs skip LLM scoring")
    ap.add_argument("--llm-model", default="claude-sonnet-4-6")
    ap.add_argument("--no-llm", action="store_true",
                    help="Skip LLM scoring (dry scores only)")
    ap.add_argument("--init-db", action="store_true")
    args = ap.parse_args()

    if args.init_db:
        init_db()
        print("DB initialized")

    stats = run_pipeline(
        remoteok_limit=args.remoteok_limit,
        wwr_limit=args.wwr_limit,
        llm_threshold=args.llm_threshold,
        llm_model=args.llm_model,
        use_llm=not args.no_llm,
    )

    print()
    print("Pipeline complete:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
