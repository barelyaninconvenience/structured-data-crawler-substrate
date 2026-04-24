# Top-33 Boards Expansion — Scope-out

**Generated:** 2026-04-24 (continued autonomous mode while Clay drives)
**For:** `scripts/job-crawler/` source-module expansion (Addendum 27 task #18 / Addendum 28 carried)
**Status:** scope-out only; no module code written. This is the planning artifact; implementation per Clay's pen.

---

## Current source coverage (8 active + 1 offline corpus)

| # | Source | Module | Auth | Style | Volume estimate |
|---|---|---|---|---|---|
| 1 | RemoteOK | `lib/sources/remoteok.py` | none (public API) | API-direct | ~500 active jobs |
| 2 | We Work Remotely | `lib/sources/wwr.py` | none (RSS) | RSS-poll | ~300 active jobs |
| 3 | Handshake | `lib/sources/handshake.py` + `handshake_playwright.py` | UC SSO + CDP | Chrome MCP / Playwright | varies (UC-scoped corpus) |
| 4 | LinkedIn | `lib/sources/linkedin.py` | LinkedIn login | Playwright/scrape | very large but rate-limited |
| 5 | Indeed | `lib/sources/indeed.py` | none (public) | scrape | very large |
| 6 | Wellfound (AngelList) | `lib/sources/wellfound.py` | account login | scrape | startup-focused, ~5K |
| 7 | ZipRecruiter | `lib/sources/ziprecruiter.py` | none (public listings) | scrape | very large |
| 8 | crawl4ai generic | `lib/sources/crawl4ai_generic.py` | any-site fallback | crawl4ai | one-off boards |
| - | Kaggle dataset | `lib/sources/kaggle_dataset.py` | none | offline corpus ingest | dataset-dependent |

**Gap to "Top 33":** ~25 additional sources.

---

## Categorization of candidate additions

Grouped by integration-cost archetype, ordered by recommended priority within each group.

### Tier A: Public API or RSS — easiest integration (5-8 boards)

These have well-documented public endpoints and can be added in 1-2 hrs each.

| Board | Endpoint type | Niche | Auth | Notes |
|---|---|---|---|---|
| **9.** Remotive | REST API (`remotive.com/api/remote-jobs`) | remote-only | none | clean JSON; easy add |
| **10.** Remote.co | RSS / scrape | remote-only, curated | none | small but high-quality |
| **11.** Working Nomads | RSS / API | remote-only | none | weekly digest, low volume |
| **12.** Jobicy | REST API | remote-only | none | similar shape to RemoteOK |
| **13.** Pangian | scrape (no RSS) | remote, international | none | useful for international + non-US time zones |
| **14.** Outsourcely | scrape | contractor / 1099-friendly | account-required for full | partial-public for first-pass |
| **15.** SkipTheDrive | RSS | remote, telecommute | none | small site but clean RSS |
| **16.** FlexJobs | scrape (paywalled) | paywalled premium | subscription | low ROI unless Clay subscribes |

### Tier B: Specialty / niche boards — moderate cost (5-7 boards)

Public scraping but require parsing-specific code. Adds breadth in overemployment-favorable niches.

| Board | Niche | Auth | Notes |
|---|---|---|---|
| **17.** Authentic Jobs | design + dev, async-friendly | none | small but quality |
| **18.** Krop | creative / design | none | overlaps with Authentic |
| **19.** Stack Overflow Jobs | dev (defunct? — verify) | n/a | check status before integrating |
| **20.** GitHub Jobs / Hacker News "Who is Hiring" | dev, monthly | none | HN parse is easy + monthly cadence |
| **21.** Dribbble Jobs | design | none | overlaps with Authentic/Krop |
| **22.** ProBlogger Job Board | content / writing | none | high task-surface-area for AI leverage |
| **23.** Behance Jobs | design / freelance | none | small |

### Tier C: Contractor / 1099 / freelance platforms — higher Detection Risk advantage (4-6 platforms)

These platforms structurally favor Detection Risk score 3 (1099 + non-exclusivity). Each has its own auth + listing surface.

| Platform | Auth | Notes |
|---|---|---|
| **24.** Upwork | account + verification | high-friction onboarding but high Detection Risk score; substantial volume |
| **25.** Toptal | application + screening | gated; only worth integrating if Clay clears their screen |
| **26.** Contra | account login | newer platform; growing |
| **27.** Worksome | account | EU-focused contractor platform |
| **28.** Braintrust | account + qualification | crypto-paid; niche but sometimes over-pays |
| **29.** Codementor / Arc | account | dev-specific; mentor + project work |

### Tier D: Geographic / international expansion (3-5 boards)

For widening the candidate pool with low-Detection-Risk international 1099 work.

| Board | Region | Notes |
|---|---|---|
| **30.** Remote OK Europe / EU Remote Jobs | EU-anchored | non-US time zones reduce Sync Oversight risk |
| **31.** Otta | UK / EU | tech-focused; well-curated |
| **32.** Honeypot | EU dev | Germany/Netherlands focus |
| **33.** Talent.com (international) | global | very large; needs filtering |
| **34.** AngelList Talent (international flag) | global startup | overlaps Wellfound but distinct facet |

### Tier E: Aggregator / meta-board — single integration, multi-source value (2-3)

| Aggregator | Notes |
|---|---|
| **35.** Adzuna (REST API, free tier) | aggregates from many boards; one integration unlocks many sources |
| **36.** Jooble (REST API) | similar aggregator pattern |
| **37.** SimplyHired | scrape; aggregator of aggregators |

---

## Recommended integration order

**Phase 1 — quick wins (Tier A, ~6 hrs total):**
- Add #9 Remotive, #10 Remote.co, #11 Working Nomads, #12 Jobicy, #15 SkipTheDrive in one batch.
- Same shape as `lib/sources/remoteok.py` — copy-and-modify pattern. Each ~1 hr including unit smoke test.
- **Outcome:** corpus expands from ~800 (current public sources) to ~1500-2000 active jobs.

**Phase 2 — aggregators (Tier E, ~4 hrs):**
- Add #35 Adzuna + #36 Jooble. Single integration each unlocks many underlying sources.
- **Outcome:** corpus expands to ~5000+ public-source jobs.

**Phase 3 — specialty niches (Tier B, ~4 hrs):**
- Add #17 Authentic Jobs, #20 HN "Who is Hiring", #22 ProBlogger.
- High signal-to-noise in overemployment-favorable niches (writing, content, async dev).
- **Outcome:** quality lift even if volume modest.

**Phase 4 — international expansion (Tier D, ~6 hrs):**
- Add #30 EU Remote, #31 Otta, #33 Talent.com.
- Critical for non-US time-zone Sync Oversight reduction.
- **Outcome:** global candidate pool; broaden to async-by-geography.

**Phase 5 — contractor platforms (Tier C, ~12 hrs total):**
- Highest auth friction; sequential not parallel.
- Order: #24 Upwork (highest volume) → #26 Contra (newer, less competition) → #25 Toptal (only after qualification screen).
- **Outcome:** Detection Risk score 3 candidates dominate the corpus; the goal posture becomes 1099-stacking.

---

## Auth complexity per integration

| Auth complexity | Boards | Effort multiplier |
|---|---|---|
| **Public API** | RemoteOK, Remotive, Jobicy, Adzuna, Jooble | ×1 (baseline ~1 hr) |
| **Public scrape (no auth)** | Indeed, ZipRecruiter, Authentic, Otta, HN | ×2 (~2 hrs each; html parsing variability) |
| **RSS** | WWR, Remote.co, Working Nomads, SkipTheDrive | ×1 (RSS is uniform) |
| **Account login (cookie-based)** | Wellfound, Outsourcely, Contra | ×3 (~3 hrs; auth + session refresh logic) |
| **Account + Playwright/CDP** | LinkedIn, Handshake, Upwork | ×5 (~5 hrs; existing pattern from Handshake reusable) |
| **Application-screened** | Toptal, Braintrust | ×5 + Clay-time gate (Clay must pass screen first) |

---

## Module-shape recommendation

For Tier A + Tier E (Phase 1 + 2), batch-create using a single template:

```python
# scripts/job-crawler/lib/sources/_template_public_api.py
from typing import Iterable
from ..normalize import NormalizedJob, parse_pay, parse_remote_status
import requests

SOURCE_NAME = "remotive"  # override per source
API_URL     = "https://remotive.com/api/remote-jobs"

def fetch_jobs(limit: int = None) -> Iterable[NormalizedJob]:
    """Yield NormalizedJob instances from this source."""
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()
    for item in payload.get("jobs", [])[:limit]:
        yield NormalizedJob(
            source=SOURCE_NAME,
            external_id=str(item["id"]),
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            url=item.get("url", ""),
            pay_raw=item.get("salary", ""),
            remote_status=parse_remote_status(item.get("candidate_required_location", "")),
            description_md=item.get("description", "")[:8000],
            scraped_at_utc=...,  # populate
        )
```

5 Tier-A modules × 1 hr each = 5 hrs total at this template level. Smoke-test pattern: `bin/scrape.py --source <name> --limit 5 --dry-run`.

---

## Database considerations

No schema changes needed. The existing `raw_jobs.source` column is `TEXT` and accepts arbitrary source names. The `sources` metadata table can have new rows added via:

```sql
INSERT INTO sources (name, url, requires_auth, scrape_method, added_at)
VALUES ('remotive', 'https://remotive.com', 0, 'api', datetime('now'));
```

Consider adding a `region` column to `sources` for Tier D international filtering: `ALTER TABLE sources ADD COLUMN region TEXT DEFAULT 'us'`.

---

## Risks and considerations

1. **Rate limiting.** Public API sources (Remotive, Jobicy, Adzuna) have rate limits; respect them with `time.sleep(1)` between calls.
2. **Duplicate handling.** `lib/dedup.py` deduplicates across sources — verify it handles new source names. Spot-check after Phase 1 batch is added.
3. **HTML drift.** Tier-B scrape sources will break when sites redesign. Add a `last_successful_fetch` column to `sources` so cron health-check can flag stale modules.
4. **Auth rotation.** Tier C contractor platforms rotate session tokens; integrate via DPAPI-stored credentials per CLAUDE.md credential standard.
5. **Legal / TOS.** Scraping Indeed, LinkedIn, ZipRecruiter is in TOS-gray territory. Public APIs (Remotive, Adzuna, Jooble) are unambiguously TOS-clean; prefer those when available.
6. **Cost tax.** Each source adds scoring volume. With v2.1 rubric requiring an Anthropic API call per job, expanding from ~800 → ~5000 jobs increases monthly Anthropic spend by ~6×. Budget gate before Phase 2 aggregators.

---

## Recommended Phase 1 execution checklist

When Clay's ready to execute Phase 1 (Tier A, ~6 hrs):

1. ☐ Verify current corpus health: `py -3.14 bin/stats.py` (existing tool)
2. ☐ Branch repo: `git checkout -b feature/top-33-phase-1`
3. ☐ Create `lib/sources/_template_public_api.py` with the template above
4. ☐ Implement `lib/sources/remotive.py` from template (smallest scope, simplest API)
5. ☐ Smoke test: `py -3.14 bin/scrape.py --source remotive --limit 5 --dry-run`
6. ☐ If clean, register: `INSERT INTO sources VALUES ('remotive', ...)`
7. ☐ Live run: `py -3.14 bin/scrape.py --source remotive --limit 100`
8. ☐ Repeat 4-7 for Jobicy, Working Nomads, Remote.co, SkipTheDrive
9. ☐ Final corpus stats, dedup spot-check
10. ☐ Merge feature branch to main; commit per Phase 1 done

**Per-source effort estimate:** 60-90 min (template + parser + smoke test + live verify).
**Phase 1 total estimate:** 5-8 hrs of focused work.

---

## What this scope-out does NOT include

- Implementation code for any new source module (this is planning only).
- Live runs or DB writes.
- Decisions about which Tier C contractor platforms Clay should personally apply to (that's a Clay-judgment call, not an engineering decision).
- Cost-benefit analysis at the application level (which sources actually convert to interviews — that requires post-corpus-collection retrospective analysis).
- TOS / legal review of scrape-against sources (Clay's call; engineering can build, deployment ethics is separate).

---

## Source: how this scope-out was generated

Reviewed:
- Existing `lib/sources/` directory (9 modules)
- `scripts/job-crawler/README.md` (architecture + current 8-source enumeration)
- `Writings/Job_Crawler_Pipeline_Design_20260423.md` (prior session's pipeline design)
- `Writings/Handshake_Job_Filter_Framework_20260423.md` (rubric origin doc)
- Public knowledge of remote-job-board landscape as of 2026 cutoff

Cross-referenced against `Writings/State_Snapshot_Current.md` Addendum 27 outstanding queue ("Top-33 boards expansion + auth handoff via Clay's secure protocol") and Addendum 28 carried-forward queue.

---

*Scope-out artifact for Top-33 boards expansion. Implementation gated on Clay's go-ahead. Phase 1 is the highest-leverage starting point: 5 Tier-A public-API sources, ~6 hrs of work, ~2-3× corpus expansion.*
