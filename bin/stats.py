#!/usr/bin/env python3
"""Report statistics on the scored-jobs corpus."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.stats import corpus_summary, format_summary
from lib.storage import connect, DEFAULT_DB


def main() -> None:
    conn = connect(DEFAULT_DB)
    summary = corpus_summary(conn)
    print(format_summary(summary))
    conn.close()


if __name__ == "__main__":
    main()
