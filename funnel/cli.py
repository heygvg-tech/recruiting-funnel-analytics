"""Command-line entry point.

    funnel report data/sample_applications.csv -o report.html
    funnel summary data/sample_applications.csv
    funnel sample -o data/sample_applications.csv
"""
from __future__ import annotations

import argparse
import json

from . import metrics, report, sample


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="funnel", description="Recruiting funnel analytics from an ATS export.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("report", help="Build an HTML report")
    r.add_argument("csv")
    r.add_argument("-o", "--out", default="report.html")
    r.add_argument("--title", default="Recruiting Funnel Report")

    s = sub.add_parser("summary", help="Print key metrics as JSON")
    s.add_argument("csv")

    g = sub.add_parser("sample", help="Generate synthetic sample data")
    g.add_argument("-o", "--out", default="data/sample_applications.csv")
    g.add_argument("-n", type=int, default=400)

    a = p.parse_args(argv)
    if a.cmd == "sample":
        sample.write_csv(a.out, sample.generate(a.n))
        print(f"Wrote {a.n} synthetic candidates to {a.out}")
        return 0

    cands = metrics.load_csv(a.csv)
    summ = metrics.summarize(cands)
    if a.cmd == "summary":
        print(json.dumps({k: v for k, v in summ.items() if k != "sources"}, indent=2, default=str))
        return 0

    html = report.render(summ, metrics.by_role(cands), title=a.title)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
