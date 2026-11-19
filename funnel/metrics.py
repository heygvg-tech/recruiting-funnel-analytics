"""Core recruiting funnel metrics computed from an ATS export.

Expected CSV columns (one row per candidate):
    candidate_id, role, department, source,
    applied_at, screen_at, hm_interview_at, onsite_at, offer_at, hired_at,
    offer_declined   (yes/no)

Stage date columns are ISO dates (YYYY-MM-DD) or blank if the candidate never
reached that stage. This shape maps cleanly onto exports from Greenhouse,
Ashby, Lever and most other ATS tools.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from statistics import median
from typing import Iterable

STAGES = ["applied", "screen", "hm_interview", "onsite", "offer", "hired"]
STAGE_LABELS = {
    "applied": "Applied",
    "screen": "Recruiter screen",
    "hm_interview": "Hiring manager",
    "onsite": "Onsite / panel",
    "offer": "Offer",
    "hired": "Hired",
}


@dataclass
class Candidate:
    candidate_id: str
    role: str
    department: str
    source: str
    dates: dict[str, date | None] = field(default_factory=dict)
    offer_declined: bool = False

    def reached(self, stage: str) -> bool:
        return self.dates.get(stage) is not None

    def furthest_stage(self) -> str:
        last = "applied"
        for s in STAGES:
            if self.reached(s):
                last = s
        return last


def _parse_date(value: str | None) -> date | None:
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def load_csv(path: str) -> list[Candidate]:
    with open(path, newline="", encoding="utf-8") as f:
        return [parse_row(row) for row in csv.DictReader(f)]


def parse_row(row: dict[str, str]) -> Candidate:
    return Candidate(
        candidate_id=row["candidate_id"],
        role=row.get("role", "").strip(),
        department=row.get("department", "").strip(),
        source=row.get("source", "").strip() or "Unknown",
        dates={s: _parse_date(row.get(f"{s}_at")) for s in STAGES},
        offer_declined=row.get("offer_declined", "").strip().lower() in {"yes", "y", "true", "1"},
    )


def stage_counts(cands: Iterable[Candidate]) -> dict[str, int]:
    cands = list(cands)
    return {s: sum(c.reached(s) for c in cands) for s in STAGES}


def pass_through(cands: Iterable[Candidate]) -> dict[str, float | None]:
    """Share of candidates at each stage who made it to the next one."""
    counts = stage_counts(cands)
    out: dict[str, float | None] = {}
    for a, b in zip(STAGES, STAGES[1:]):
        out[f"{a}->{b}"] = counts[b] / counts[a] if counts[a] else None
    return out


def days_in_stage(cands: Iterable[Candidate]) -> dict[str, float | None]:
    """Median days candidates spent in a stage before moving to the next."""
    out: dict[str, float | None] = {}
    cands = list(cands)
    for a, b in zip(STAGES, STAGES[1:]):
        gaps = [(c.dates[b] - c.dates[a]).days for c in cands if c.dates.get(a) and c.dates.get(b)]
        out[a] = median(gaps) if gaps else None
    return out


def time_to_hire(cands: Iterable[Candidate]) -> float | None:
    """Median days from application to hire."""
    gaps = [(c.dates["hired"] - c.dates["applied"]).days for c in cands
            if c.dates.get("hired") and c.dates.get("applied")]
    return median(gaps) if gaps else None


def offer_acceptance(cands: Iterable[Candidate]) -> float | None:
    cands = list(cands)
    offers = [c for c in cands if c.reached("offer")]
    if not offers:
        return None
    return sum(c.reached("hired") for c in offers) / len(offers)


def source_breakdown(cands: Iterable[Candidate]) -> list[dict]:
    """Volume and quality by source: how many applied, screened, and were hired."""
    by_source: dict[str, list[Candidate]] = {}
    for c in cands:
        by_source.setdefault(c.source, []).append(c)
    rows = []
    for src, group in by_source.items():
        hired = sum(c.reached("hired") for c in group)
        rows.append({
            "source": src,
            "candidates": len(group),
            "screened": sum(c.reached("screen") for c in group),
            "hired": hired,
            "hire_rate": hired / len(group) if group else 0.0,
        })
    return sorted(rows, key=lambda r: (-r["hired"], -r["candidates"]))


def bottleneck(cands: Iterable[Candidate]) -> str | None:
    """The stage transition with the lowest pass-through: where searches stall."""
    pt = {k: v for k, v in pass_through(cands).items() if v is not None}
    return min(pt, key=pt.get) if pt else None


def summarize(cands: list[Candidate]) -> dict:
    return {
        "candidates": len(cands),
        "counts": stage_counts(cands),
        "pass_through": pass_through(cands),
        "days_in_stage": days_in_stage(cands),
        "time_to_hire": time_to_hire(cands),
        "offer_acceptance": offer_acceptance(cands),
        "sources": source_breakdown(cands),
        "bottleneck": bottleneck(cands),
    }


def by_role(cands: list[Candidate]) -> dict[str, dict]:
    roles: dict[str, list[Candidate]] = {}
    for c in cands:
        roles.setdefault(c.role, []).append(c)
    return {r: summarize(g) for r, g in sorted(roles.items())}
