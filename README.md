# recruiting-funnel-analytics

Turn a plain ATS export into the recruiting metrics hiring managers actually ask about: **pass-through by stage, time in stage, time to hire, offer acceptance, and source of hire**, plus a one-page HTML report that flags where searches are stalling.

I'm a technical recruiter, and I built this because most ATS dashboards make it hard to answer simple questions like *"Where are we losing candidates?"* or *"Are referrals actually better than inbound?"* This runs on a CSV in seconds, with no dependencies beyond Python.

![tests](https://github.com/heygvg-tech/recruiting-funnel-analytics/actions/workflows/ci.yml/badge.svg)

**[View the live sample report →](https://heygvg-tech.github.io/recruiting-funnel-analytics/sample_report.html)**

## What it does

| Metric | Why it matters |
|---|---|
| **Pass-through rate** per stage | Shows whether the problem is sourcing, calibration, or the interview loop |
| **Median time in stage** | Finds slow feedback and scheduling delays |
| **Time to hire** | Keeps hiring plans honest |
| **Offer acceptance** | Signals comp or closing issues |
| **Source of hire** | Shows which channels produce hires, not just applicants |
| **Bottleneck** | Automatically highlights the stage with the biggest drop-off |

All metrics can be broken down **by role**.

## Quick start

```bash
pip install -e .
funnel sample -o data/sample_applications.csv      # synthetic demo data
funnel report data/sample_applications.csv -o report.html
funnel summary data/sample_applications.csv       # JSON for a quick look
```

Open `report.html` in a browser, or see [`docs/sample_report.html`](docs/sample_report.html).

## Input format

One row per candidate. Stage columns are dates (`YYYY-MM-DD`), blank if the candidate never reached that stage:

```
candidate_id,role,department,source,applied_at,screen_at,hm_interview_at,onsite_at,offer_at,hired_at,offer_declined
C0001,ML Engineer,Engineering,Referral,2026-02-03,2026-02-06,2026-02-12,2026-02-19,2026-02-24,2026-02-27,no
```

This maps onto exports from Greenhouse, Ashby, Lever and most other ATS tools with a quick column rename.

## Project layout

```
funnel/
  metrics.py   # pure functions: counts, pass-through, time in stage, sources, bottleneck
  report.py    # self-contained HTML report with an inline SVG funnel
  sample.py    # deterministic synthetic data generator
  cli.py       # `funnel report | summary | sample`
tests/         # pytest suite, run in CI on every push
```

## Notes

- Sample data is **fully synthetic**. No real candidate data is included or required.
- Built with help from AI coding tools, then reviewed, tested and shaped around how recruiting teams actually work.

## Roadmap

- Direct import from the Greenhouse and Ashby APIs
- Week-over-week trend charts
- Hiring manager feedback-time leaderboard
