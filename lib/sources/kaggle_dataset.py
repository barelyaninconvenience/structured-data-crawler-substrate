"""Ingest job postings from a downloaded Kaggle dataset (CSV/JSON/Parquet).

Kaggle datasets come as zipped archives of tabular files. This module:
    1. Downloads a dataset via the Kaggle CLI (requires ~/.kaggle/kaggle.json).
    2. Unzips into data/kaggle/<dataset-slug>/.
    3. Auto-detects the primary file (CSV preferred).
    4. Maps columns to NormalizedJob fields using a configurable map.
    5. Iterates + yields NormalizedJob objects.

Usage (from a calling script):
    from lib.sources.kaggle_dataset import download_and_ingest
    for job in download_and_ingest(
        "jessysisca/job-descriptions-and-remote-task-descriptions",
        column_map={
            "title": "job_title",
            "company": "employer_name",
            "description": "job_description",
            "pay": "salary",
        },
    ):
        yield job
"""

from __future__ import annotations

import csv
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Iterator, Optional

from ..normalize import NormalizedJob, make_normalized_job


DEFAULT_COLUMN_MAP = {
    "title": ["job_title", "title", "position", "role", "Job Title"],
    "company": ["company_name", "company", "employer", "organization", "Company"],
    "description": ["job_description", "description", "details", "summary", "Job Description"],
    "pay": ["salary", "pay", "compensation", "salary_range", "Salary"],
    "url": ["job_url", "url", "link", "posting_url"],
    "location": ["location", "city", "job_location", "Location"],
    "posted_date": ["posted_date", "date", "date_posted", "posting_date"],
}


def download_dataset(dataset_slug: str, out_dir: Path) -> Path:
    """Download + unzip a Kaggle dataset. Returns the extracted folder path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / dataset_slug.replace("/", "--")
    target.mkdir(exist_ok=True)

    cmd = ["kaggle", "datasets", "download",
           "-d", dataset_slug,
           "-p", str(target),
           "--unzip"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"kaggle download failed (exit {result.returncode})")
    print(result.stdout)
    return target


def _detect_primary_file(dataset_dir: Path) -> Path:
    """Pick the most-likely primary data file in the dataset."""
    # Prefer CSV > JSON > Parquet; pick the largest of each type
    for ext in ["csv", "json", "jsonl", "parquet"]:
        matches = list(dataset_dir.glob(f"*.{ext}"))
        if matches:
            return max(matches, key=lambda p: p.stat().st_size)
    # Fallback: any file
    all_files = [f for f in dataset_dir.iterdir() if f.is_file()]
    if not all_files:
        raise FileNotFoundError(f"no data files found in {dataset_dir}")
    return max(all_files, key=lambda p: p.stat().st_size)


def _pick_column(row: dict, candidates: list[str]) -> str:
    """Pick the first matching column name from a row's keys."""
    for c in candidates:
        if c in row and row[c]:
            return str(row[c])
        # Case-insensitive match
        for k in row.keys():
            if k.lower() == c.lower() and row[k]:
                return str(row[k])
    return ""


def ingest_csv(
    path: Path, column_map: Optional[dict] = None, source: str = "kaggle",
    limit: Optional[int] = None,
) -> Iterator[NormalizedJob]:
    """Iterate rows of a CSV and yield NormalizedJob objects."""
    cmap = {**DEFAULT_COLUMN_MAP, **(column_map or {})}
    # If column_map values are strings (single-name mapping), convert to lists
    for k, v in list(cmap.items()):
        if isinstance(v, str):
            cmap[k] = [v]

    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = _pick_column(row, cmap["title"])
            if not title:
                continue
            company = _pick_column(row, cmap["company"])
            description = _pick_column(row, cmap["description"])
            pay = _pick_column(row, cmap["pay"])
            url = _pick_column(row, cmap["url"]) or f"kaggle://{path.name}/row-{count}"
            posted = _pick_column(row, cmap["posted_date"])

            yield make_normalized_job(
                source=source,
                source_url=url,
                title=title,
                company=company,
                pay_raw=pay,
                description_md=description,
                posted_date=posted,
            )
            count += 1
            if limit and count >= limit:
                break


def ingest_json(
    path: Path, column_map: Optional[dict] = None, source: str = "kaggle",
    limit: Optional[int] = None,
) -> Iterator[NormalizedJob]:
    """Iterate a JSON or JSONL file."""
    cmap = {**DEFAULT_COLUMN_MAP, **(column_map or {})}
    for k, v in list(cmap.items()):
        if isinstance(v, str):
            cmap[k] = [v]

    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        # Try JSONL first (one JSON object per line); fall back to a JSON array
        f.seek(0)
        first_char = f.read(1)
        f.seek(0)
        if first_char == "[":
            rows = json.load(f)
        else:
            rows = (json.loads(line) for line in f if line.strip())

        for row in rows:
            if not isinstance(row, dict):
                continue
            title = _pick_column(row, cmap["title"])
            if not title:
                continue
            yield make_normalized_job(
                source=source,
                source_url=_pick_column(row, cmap["url"]) or f"kaggle://{path.name}/row-{count}",
                title=title,
                company=_pick_column(row, cmap["company"]),
                pay_raw=_pick_column(row, cmap["pay"]),
                description_md=_pick_column(row, cmap["description"]),
                posted_date=_pick_column(row, cmap["posted_date"]),
            )
            count += 1
            if limit and count >= limit:
                break


def download_and_ingest(
    dataset_slug: str,
    column_map: Optional[dict] = None,
    out_dir: Optional[Path] = None,
    limit: Optional[int] = None,
) -> Iterator[NormalizedJob]:
    """Download a Kaggle dataset + yield NormalizedJob objects.

    Requires `kaggle` CLI authenticated (see https://github.com/Kaggle/kaggle-api).

    Args:
        dataset_slug: e.g., "jessysisca/job-descriptions-and-remote-task-descriptions"
        column_map: optional override mapping NormalizedJob fields to CSV columns
        out_dir: where to store the downloaded dataset (default: data/kaggle/)
        limit: max rows to yield
    """
    if out_dir is None:
        out_dir = Path(__file__).resolve().parent.parent.parent / "data" / "kaggle"
    dataset_dir = download_dataset(dataset_slug, out_dir)
    primary = _detect_primary_file(dataset_dir)
    print(f"Primary file: {primary.name} ({primary.stat().st_size:,} bytes)")
    source_name = f"kaggle:{dataset_slug}"
    if primary.suffix.lower() == ".csv":
        yield from ingest_csv(primary, column_map, source=source_name, limit=limit)
    elif primary.suffix.lower() in (".json", ".jsonl"):
        yield from ingest_json(primary, column_map, source=source_name, limit=limit)
    else:
        raise NotImplementedError(f"file type {primary.suffix} not yet supported")
