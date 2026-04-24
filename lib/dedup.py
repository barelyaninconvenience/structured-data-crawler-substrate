"""Deduplication: detect same job posted across multiple boards."""

from __future__ import annotations

import hashlib
from rapidfuzz import fuzz


def dedup_signature(title: str, company: str) -> str:
    """Canonical signature for identity comparison."""
    t = (title or "").lower().strip()
    c = (company or "").lower().strip()
    # Normalize common noise
    for token in [" - remote", " (remote)", " | remote", "senior ", "sr. ", "jr. "]:
        t = t.replace(token, " ")
    t = " ".join(t.split())
    return hashlib.sha256(f"{t}|{c}".encode("utf-8")).hexdigest()[:16]


def fuzzy_match_score(t1: str, c1: str, t2: str, c2: str) -> float:
    """0-100 similarity between two (title, company) pairs."""
    title_score = fuzz.token_set_ratio(t1 or "", t2 or "")
    company_score = fuzz.token_set_ratio(c1 or "", c2 or "")
    return 0.6 * title_score + 0.4 * company_score


def find_duplicates(jobs: list[tuple[str, str, str]], threshold: float = 85.0) -> list[list[str]]:
    """Given a list of (id, title, company) tuples, return groups of likely-duplicate IDs.

    Uses fuzzy matching; threshold of 85 is conservative (catches rewordings,
    avoids false positives on common titles like 'Software Engineer')."""
    groups: list[list[str]] = []
    assigned: set[str] = set()
    for i, (id_i, t_i, c_i) in enumerate(jobs):
        if id_i in assigned:
            continue
        group = [id_i]
        assigned.add(id_i)
        for id_j, t_j, c_j in jobs[i + 1:]:
            if id_j in assigned:
                continue
            if fuzzy_match_score(t_i, c_i, t_j, c_j) >= threshold:
                group.append(id_j)
                assigned.add(id_j)
        if len(group) > 1:
            groups.append(group)
    return groups
