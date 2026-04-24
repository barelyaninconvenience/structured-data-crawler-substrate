"""Normalized job schema + parsers for pay / remote / location."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class NormalizedJob:
    id: str
    source: str
    source_url: str
    title: str
    company: str = ""
    pay_raw: str = ""
    pay_min: Optional[int] = None
    pay_max: Optional[int] = None
    pay_type: str = "unknown"        # 'hourly', 'annual', 'unknown'
    remote_status: str = "unclear"   # 'fully_remote', 'hybrid', 'onsite', 'unclear'
    location: str = ""
    description_md: str = ""
    posted_date: str = ""
    scraped_at: str = ""
    raw_html_path: str = ""
    dedup_group_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def make_job_id(source_url: str, title: str, company: str) -> str:
    """Stable 16-char ID from the job's identity."""
    signature = f"{source_url}|{title.lower().strip()}|{company.lower().strip()}"
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16]


# ── Pay parsing ──────────────────────────────────────────────────────────────

_PAY_RANGE_RE = re.compile(
    r"\$?\s*(\d{2,6}(?:,\d{3})?(?:\.\d+)?)\s*k?\s*[-–—]\s*\$?\s*(\d{2,6}(?:,\d{3})?(?:\.\d+)?)\s*k?",
    re.IGNORECASE,
)
_PAY_SINGLE_RE = re.compile(
    r"\$?\s*(\d{2,6}(?:,\d{3})?(?:\.\d+)?)\s*(k|K)?",
)
_HOURLY_RE = re.compile(r"/\s*(hr|hour|h)\b", re.IGNORECASE)
_ANNUAL_RE = re.compile(r"/\s*(yr|year|y|annually)\b", re.IGNORECASE)


def parse_pay(raw: str) -> tuple[Optional[int], Optional[int], str]:
    """Return (min, max, type) from a pay string.

    Handles formats like:
        $50,000 - $80,000
        $50k-$80k
        $25/hr
        50k
        60000 per year
    """
    if not raw:
        return None, None, "unknown"

    # Determine type first
    if _HOURLY_RE.search(raw):
        pay_type = "hourly"
    elif _ANNUAL_RE.search(raw):
        pay_type = "annual"
    elif "hourly" in raw.lower():
        pay_type = "hourly"
    elif any(tok in raw.lower() for tok in ["salary", "per year", "annually"]):
        pay_type = "annual"
    else:
        pay_type = "unknown"

    def _to_int(s: str) -> Optional[int]:
        s = s.replace(",", "").strip()
        try:
            v = float(s)
            return int(v)
        except ValueError:
            return None

    # Try range first
    m = _PAY_RANGE_RE.search(raw)
    if m:
        a = _to_int(m.group(1))
        b = _to_int(m.group(2))
        has_k = "k" in raw.lower()
        if has_k:
            if a is not None and a < 1000: a *= 1000
            if b is not None and b < 1000: b *= 1000
        # Infer type from magnitude if unknown
        if pay_type == "unknown":
            if a is not None and a < 200:
                pay_type = "hourly"
            elif a is not None and a >= 1000:
                pay_type = "annual"
        return a, b, pay_type

    # Try single value
    m = _PAY_SINGLE_RE.search(raw)
    if m:
        a = _to_int(m.group(1))
        k = m.group(2)
        if k and a is not None and a < 1000:
            a *= 1000
        if pay_type == "unknown":
            if a is not None and a < 200:
                pay_type = "hourly"
            elif a is not None and a >= 1000:
                pay_type = "annual"
        return a, None, pay_type

    return None, None, pay_type


def annual_equivalent(pay_min: Optional[int], pay_type: str) -> Optional[int]:
    """Convert hourly/annual to approximate annual USD."""
    if pay_min is None:
        return None
    if pay_type == "annual":
        return pay_min
    if pay_type == "hourly":
        return pay_min * 2080  # 40 hours/week × 52 weeks
    return None


# ── Remote status parsing ────────────────────────────────────────────────────

_FULLY_REMOTE_PATTERNS = [
    r"\bfully\s+remote\b",
    r"\b100%\s+remote\b",
    r"\bremote\s+anywhere\b",
    r"\bwork\s+from\s+anywhere\b",
    r"\bremote\s+ok\b",
    r"\bremote\s+(role|position|job)\b",
]

_HYBRID_PATTERNS = [
    r"\bhybrid\b",
    r"\bremote\s+hybrid\b",
    r"\b\d+\s+days?\s+(in|per\s+week)\s+office\b",
    r"\bremote\s+with\s+(occasional|quarterly|periodic)\s+(travel|visits?|in[- ]office)\b",
]

_ONSITE_PATTERNS = [
    r"\bon[- ]?site\b",
    r"\bin[- ]office\b",
    r"\bmust\s+be\s+located\s+in\b",
    r"\blocal\s+candidates\s+only\b",
]


def parse_remote_status(text: str) -> str:
    t = text.lower()
    # Check hybrid BEFORE onsite: 'Hybrid 2 days in office' contains 'in office' but is hybrid.
    for p in _HYBRID_PATTERNS:
        if re.search(p, t):
            return "hybrid"
    for p in _ONSITE_PATTERNS:
        if re.search(p, t):
            return "onsite"
    for p in _FULLY_REMOTE_PATTERNS:
        if re.search(p, t):
            return "fully_remote"
    if "remote" in t:
        return "fully_remote"
    return "unclear"


# ── Location parsing ─────────────────────────────────────────────────────────

_STATE_ABBRS = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}
_LOCATION_RE = re.compile(r"([A-Z][a-zA-Z .]+),\s*([A-Z]{2})\b")


def parse_location(text: str) -> str:
    """Best-effort 'City, ST' extraction."""
    m = _LOCATION_RE.search(text)
    if m and m.group(2) in _STATE_ABBRS:
        return f"{m.group(1).strip()}, {m.group(2)}"
    return ""


# ── Construction helper ──────────────────────────────────────────────────────

def make_normalized_job(
    *,
    source: str,
    source_url: str,
    title: str,
    company: str = "",
    pay_raw: str = "",
    description_md: str = "",
    posted_date: str = "",
    raw_html_path: str = "",
) -> NormalizedJob:
    job_id = make_job_id(source_url, title, company)
    pay_min, pay_max, pay_type = parse_pay(pay_raw)
    remote_status = parse_remote_status(description_md + " " + pay_raw + " " + title)
    location = parse_location(description_md)
    return NormalizedJob(
        id=job_id,
        source=source,
        source_url=source_url,
        title=title.strip(),
        company=company.strip(),
        pay_raw=pay_raw.strip(),
        pay_min=pay_min,
        pay_max=pay_max,
        pay_type=pay_type,
        remote_status=remote_status,
        location=location,
        description_md=description_md.strip(),
        posted_date=posted_date,
        scraped_at=datetime.now(timezone.utc).isoformat(),
        raw_html_path=raw_html_path,
    )
