# Structured Data Crawler Substrate
## A general-purpose framework for multi-source structured-data extraction with LLM-based scoring

**A reusable substrate for "scrape from N sources → normalize to common schema → score with LLM rubric → store + shortlist + act."**

This pattern is domain-agnostic — applied here to job listings as the worked example, but the same architecture applies to any structured-data domain (Canvas course pages, GitHub repo discovery, paper preprint feeds, etc.).

**Companion to:** [Substrate Thesis Companion](https://github.com/barelyaninconvenience/substrate-thesis-companion) — this repo is a worked example of the cross-domain SRD (Stable Recursive Decomposition) pattern from that framework. See `Substrate_Thesis_Companion/case_studies/04_job_crawler_cross_domain_substrate.md` for the architectural framing.

---

## Quick example

```bash
# Install deps
pip install -r requirements.txt

# Initialize SQLite store
sqlite3 data/items.db < schema.sql

# Scrape a public source (no auth required)
python bin/scrape.py --source remoteok --limit 50

# Score unscored items with LLM rubric
export ANTHROPIC_API_KEY=...
python bin/score.py --limit 50

# Export shortlist (recommended ≥ 9 score)
python bin/shortlist.py --min-score 9 --out data/shortlist.csv
```

---

## Architecture (the substrate)

```
Source-specific fetch  →  normalize (common schema)  →  LLM rubric score  →  store  →  shortlist
       ↑                          ↑                              ↑                ↑          ↑
  per-source module     NormalizedJob dataclass         lib/score.py        SQLite      v_shortlist
```

Five-stage pipeline. Same structural shape regardless of source diversity. To add a new source: implement `fetch_all() → Iterator[NormalizedJob]` per the existing source-module template.

---

## Sources included

13 public source modules (no auth required):

| Source | Type | Scope |
|---|---|---|
| RemoteOK | REST API | Remote-only jobs |
| Remotive | REST API | Remote-only jobs |
| Jobicy | REST API | Remote-only jobs |
| Working Nomads | JSON + RSS | Remote-only jobs |
| Remote.co | RSS (per-category) | Remote-only jobs |
| SkipTheDrive | RSS (per-category) | Remote-only jobs |
| We Work Remotely | RSS (per-category) | Remote-only jobs |
| Indeed | crawl4ai | General job search |
| Wellfound | crawl4ai | Startup roles |
| ZipRecruiter | crawl4ai | General job search |
| crawl4ai_generic | Any-site fallback | Generic web pattern |
| Kaggle Dataset Ingest | offline | Pre-collected corpora |

**Authenticated source modules (LinkedIn, Handshake) are intentionally NOT included** — auth-handling code reveals deployer-specific patterns. Use the source-module template in `docs/` to implement your own auth-required sources locally.

---

## Source-module template

To add a source `<NAME>`:

```python
# lib/sources/<name>.py
from __future__ import annotations
import time
from typing import Iterator
import httpx  # or feedparser for RSS
from ..normalize import NormalizedJob, make_normalized_job

API_URL = "https://example.com/api/jobs"
SOURCE_NAME = "<name>"


def fetch_all(limit: int | None = None) -> Iterator[NormalizedJob]:
    headers = {"User-Agent": "structured-data-crawler/1.0"}
    with httpx.Client(timeout=30, headers=headers) as client:
        r = client.get(API_URL)
        r.raise_for_status()
        data = r.json()

    count = 0
    for item in data.get("jobs", []):
        yield make_normalized_job(
            source=SOURCE_NAME,
            source_url=item["url"],
            title=item["title"],
            company=item.get("company", ""),
            pay_raw=item.get("salary", ""),
            description_md=item.get("description", ""),
            posted_date=item.get("posted", ""),
        )
        count += 1
        if limit and count >= limit:
            break
        time.sleep(0.05)  # polite
```

Then register in `bin/scrape.py` source registry.

---

## v1 rubric (6 dimensions, equal-weighted)

The included `rubric.md` documents a generic 6-dimension scoring rubric appropriate for personal job filtering: Automatability, Oversight, Pay, Remote, Stakes, Flexibility. Each scored 0-2; total 0-12.

**This is a STARTING POINT.** Effective scoring rubrics depend on your specific use case. The v1 rubric here is intentionally generic; consumers should fork + tune to their needs.

For domain-specific rubrics with more dimensions + weighted-sum + multipliers + vetoes, see `docs/Top33_Boards_Scopeout_20260424.md` for the architectural pattern (the linked deployer customizes their own rubric privately).

---

## What's NOT in this repo

By design, the following are NOT public:
- **Authenticated source modules** (LinkedIn, Handshake, etc.) — auth-handling reveals deployer-specific patterns
- **Specific scoring tunings beyond v1 generic rubric** — domain-specific tuning is the deployer's competitive advantage to develop privately
- **Operational data** — your scraped corpus + scoring results are yours alone
- **Deployer-specific MCPs / Claude Code skills / slash commands** — those are integration patterns specific to a given deployer's workflow

The architectural pattern is public; deployer-specific tuning + auth is private. This split is documented as a Substrate Thesis case study (cross-domain SRD with public/private contract).

---

## Repository structure

```
structured-data-crawler-substrate/
├── README.md (this file)
├── LICENSE (MIT)
├── requirements.txt
├── schema.sql (SQLite v1 schema with v_shortlist view)
├── rubric.md (v1 6-dimension rubric definition)
├── lib/
│   ├── normalize.py (NormalizedJob dataclass + parsers for pay / remote / location)
│   ├── score.py (v1 LLM scoring against 6-dim rubric)
│   ├── storage.py (SQLite helpers: connect, init_db, insert_job, unscored_jobs, save_score, shortlist)
│   ├── dedup.py (cross-source duplicate detection)
│   ├── cover_letter.py (tailored application material generation)
│   └── sources/ (13 source modules)
├── bin/
│   ├── scrape.py (unified scraping CLI)
│   ├── score.py (batch scoring CLI)
│   ├── dry_score.py (preview scoring without DB writes)
│   ├── dedupe.py (deduplication CLI)
│   ├── shortlist.py (export CSV)
│   ├── cover_letter.py (per-job cover letter generation)
│   ├── stats.py (corpus statistics)
│   ├── smoke_test.py (integration smoke test)
│   ├── ingest_kaggle.py (offline dataset ingest)
│   ├── apply_tracker.py (application status tracking)
│   └── pipeline.py (end-to-end runner)
└── docs/
    └── Top33_Boards_Scopeout_20260424.md (multi-source expansion strategy)
```

---

## Contributing

PRs welcome for:
- New public-API source modules (use the source template above)
- Improvements to `normalize.py` parsing (pay strings, remote-status detection, location parsing)
- Generic dedup heuristics
- Tests + smoke-test additions

Please do NOT contribute:
- Authenticated source modules (use them locally)
- Domain-specific rubric tunings (fork + maintain in your own repo)

---

## License

MIT — use freely, modify freely, redistribute freely. Attribution appreciated but not required.

---

## Background + lineage

This repo is the public substrate split out of a private domain-specific deployment. The architecture pattern (scrape → normalize → score → store → shortlist) is general; the public split exists to share the substrate while letting deployers maintain their domain-specific calibrations privately.

For the architectural framing, see [Substrate Thesis Companion](https://github.com/barelyaninconvenience/substrate-thesis-companion).

For the source-expansion strategy informing the 13-source roster, see `docs/Top33_Boards_Scopeout_20260424.md`.

---

*Generated 2026-04-24. Public substrate companion to a private domain-specific deployment. Architecture-public, calibrations-private split.*
