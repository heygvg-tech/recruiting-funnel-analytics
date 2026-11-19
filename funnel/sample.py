"""Generate realistic, fully synthetic ATS data for demos and tests."""
from __future__ import annotations

import csv
import os
import random
from datetime import date, timedelta

ROLES = [
    ("Senior Software Engineer", "Engineering"),
    ("ML Engineer", "Engineering"),
    ("Product Designer", "Design"),
    ("Account Executive", "Sales"),
]
# (source, weight, quality multiplier)
SOURCES = [("Sourced (LinkedIn)", 0.30, 1.6), ("Referral", 0.15, 2.0),
           ("Inbound", 0.45, 0.6), ("Agency", 0.10, 1.1)]
# baseline odds of advancing, and typical days spent, per stage
ADVANCE = {"applied": 0.35, "screen": 0.55, "hm_interview": 0.45, "onsite": 0.40, "offer": 0.85}
DAYS = {"applied": 4, "screen": 5, "hm_interview": 7, "onsite": 6, "offer": 4}
ORDER = ["applied", "screen", "hm_interview", "onsite", "offer", "hired"]


def generate(n: int = 400, seed: int = 7, start: date = date(2026, 1, 5)) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        role, dept = rng.choice(ROLES)
        src, _, quality = rng.choices(SOURCES, weights=[s[1] for s in SOURCES])[0]
        d = start + timedelta(days=rng.randint(0, 240))
        row = {"candidate_id": f"C{i:04d}", "role": role, "department": dept, "source": src,
               **{f"{s}_at": "" for s in ORDER}, "offer_declined": "no"}
        row["applied_at"] = d.isoformat()
        for cur, nxt in zip(ORDER, ORDER[1:]):
            boost = quality if cur == "applied" else 1 + (quality - 1) / 4
            p = ADVANCE[cur] if cur == "offer" else min(0.9, ADVANCE[cur] * boost)
            if rng.random() > p:
                if cur == "offer":
                    row["offer_declined"] = "yes"
                break
            d += timedelta(days=max(1, round(rng.gauss(DAYS[cur], 2))))
            row[f"{nxt}_at"] = d.isoformat()
        rows.append(row)
    return rows


def write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
