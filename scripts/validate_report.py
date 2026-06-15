#!/usr/bin/env python3
"""Validate latest daily report against v2 KPI targets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS_JSON = ROOT / "data" / "news.json"

NOISE_MARKERS = (
    "airline",
    "pilot",
    "driver license",
    "crypto",
    "bitcoin",
)


def load_latest_report() -> dict | None:
    if not NEWS_JSON.exists():
        return None
    data = json.loads(NEWS_JSON.read_text(encoding="utf-8"))
    reports = data.get("reports") or []
    if not reports:
        return None
    return reports[0]


def item_origin(item: dict) -> str:
    origin = item.get("origin")
    if origin in ("domestic", "global"):
        return origin
    if item.get("section") == "domestic":
        return "domestic"
    return "global"


def main() -> int:
    report = load_latest_report()
    if not report:
        print("No report found.")
        return 1

    date = report.get("reportDate", "?")
    items = report.get("items") or []
    highlights = report.get("executiveHighlights") or []

    domestic = sum(1 for i in items if item_origin(i) == "domestic")
    paper = sum(1 for i in items if i.get("section") == "paper")
    top10 = sorted(items, key=lambda x: -(x.get("investorRelevanceScore") or x.get("importanceScore") or 0))[:10]
    top10_domestic = sum(1 for i in top10 if item_origin(i) == "domestic")

    noise_top10 = [
        i["title"]
        for i in top10
        if any(m in i.get("title", "").lower() for m in NOISE_MARKERS)
    ]
    empty_takeaway = sum(
        1 for i in items if not str(i.get("investmentTakeaway") or i.get("significance") or "").strip()
    )

    print(f"Report: {date}")
    print(f"  items: {len(items)}")
    print(f"  domestic origin: {domestic} ({domestic / max(len(items), 1) * 100:.0f}%)")
    print(f"  paper section: {paper}")
    print(f"  executiveHighlights: {len(highlights)}")
    print(f"  top10 domestic: {top10_domestic}")
    print(f"  empty investmentTakeaway: {empty_takeaway}")

    ok = True
    if len(items) > 0 and domestic < 8:
        print(f"  [FAIL] domestic {domestic} < 8")
        ok = False
    if paper > 3:
        print(f"  [FAIL] paper {paper} > 3")
        ok = False
    if top10_domestic < 2 and len(items) >= 10:
        print(f"  [FAIL] top10 domestic {top10_domestic} < 2")
        ok = False
    if noise_top10:
        print("  [FAIL] noise in top10:")
        for t in noise_top10[:3]:
            print(f"    - {t[:100]}")
        ok = False
    if empty_takeaway > 0:
        print(f"  [FAIL] empty takeaway: {empty_takeaway}")
        ok = False

    if ok:
        print("  [PASS] KPI checks passed")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
