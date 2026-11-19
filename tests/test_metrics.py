from datetime import date

from funnel import metrics, report, sample


def row(cid, applied, screen="", hm="", onsite="", offer="", hired="", src="Referral", declined="no"):
    return metrics.parse_row({
        "candidate_id": cid, "role": "SWE", "department": "Eng", "source": src,
        "applied_at": applied, "screen_at": screen, "hm_interview_at": hm,
        "onsite_at": onsite, "offer_at": offer, "hired_at": hired, "offer_declined": declined,
    })


CANDS = [
    row("1", "2026-01-01", "2026-01-03", "2026-01-10", "2026-01-15", "2026-01-18", "2026-01-21"),
    row("2", "2026-01-01", "2026-01-05", "2026-01-12", "2026-01-20", "2026-01-25", declined="yes"),
    row("3", "2026-01-02", "2026-01-04", src="Inbound"),
    row("4", "2026-01-02", src="Inbound"),
]


def test_stage_counts():
    c = metrics.stage_counts(CANDS)
    assert c == {"applied": 4, "screen": 3, "hm_interview": 2, "onsite": 2, "offer": 2, "hired": 1}


def test_pass_through():
    pt = metrics.pass_through(CANDS)
    assert pt["applied->screen"] == 0.75
    assert pt["offer->hired"] == 0.5


def test_time_to_hire_and_offer_acceptance():
    assert metrics.time_to_hire(CANDS) == 20
    assert metrics.offer_acceptance(CANDS) == 0.5


def test_days_in_stage_uses_median():
    d = metrics.days_in_stage(CANDS)
    gaps = sorted([(date(2026, 1, 3) - date(2026, 1, 1)).days,   # 2
                   (date(2026, 1, 5) - date(2026, 1, 1)).days,   # 4
                   (date(2026, 1, 4) - date(2026, 1, 2)).days])  # 2
    assert d["applied"] == gaps[1] == 2


def test_bottleneck_is_lowest_pass_through():
    assert metrics.bottleneck(CANDS) == "offer->hired"


def test_source_breakdown_ranks_by_hires():
    rows = metrics.source_breakdown(CANDS)
    assert rows[0]["source"] == "Referral" and rows[0]["hired"] == 1


def test_report_renders_and_sample_is_deterministic():
    data = [metrics.parse_row(r) for r in sample.generate(50, seed=1)]
    html = report.render(metrics.summarize(data), metrics.by_role(data))
    assert "<svg" in html and "Source of hire" in html
    assert sample.generate(10, seed=3) == sample.generate(10, seed=3)
