#!/usr/bin/env python3
"""Generate a cover letter for a specific scored job."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.cover_letter import generate_cover_letter
from lib.storage import connect, DEFAULT_DB


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--resume", type=Path, required=True,
                    help="Path to resume markdown")
    ap.add_argument("--voice-sample", type=Path, default=None,
                    help="Optional voice sample markdown")
    ap.add_argument("--context", type=str, default="",
                    help="Additional context for the letter")
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    conn = connect(DEFAULT_DB)
    row = conn.execute(
        "SELECT * FROM raw_jobs WHERE id = ?", (args.job_id,)
    ).fetchone()
    if not row:
        print(f"job {args.job_id} not found")
        sys.exit(1)

    resume = args.resume.read_text(encoding="utf-8")
    voice = args.voice_sample.read_text(encoding="utf-8") if args.voice_sample else ""

    letter = generate_cover_letter(
        job_title=row["title"],
        job_company=row["company"] or "",
        job_description=row["description_md"] or "",
        resume_markdown=resume,
        voice_sample=voice,
        additional_context=args.context,
        model=args.model,
    )

    if not args.out:
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        slug = (row["company"] or "unknown").replace(" ", "_").lower()[:30]
        args.out = DEFAULT_DB.parent / "cover_letters" / f"{stamp}_{slug}_{args.job_id}.md"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(letter, encoding="utf-8")
    print(f"wrote → {args.out}")

    # Track in applications table
    conn.execute(
        """INSERT OR REPLACE INTO applications (job_id, status, cover_letter_path, resume_path)
           VALUES (?, COALESCE((SELECT status FROM applications WHERE job_id = ?), 'not_applied'), ?, ?)""",
        (args.job_id, args.job_id, str(args.out), str(args.resume)),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
