#!/usr/bin/env python3
"""
PH6 Evidence Campaign Report v1.0

Reads campaign_matrix.json and reports current status of each evidence campaign.
Shows what is OPEN, what prerequisites are blocking, and what is required to proceed.

Does not modify any campaign status. Status updates are human-only.

Usage:
  python3 ph6_evidence_campaign_report.py
  python3 ph6_evidence_campaign_report.py --campaign EVC-03
  python3 ph6_evidence_campaign_report.py --json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


_SOURCE_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MATRIX_PATH   = os.path.join(_SOURCE_ROOT, "VALIDATION", "campaign_matrix.json")
_DIVIDER       = "=" * 72
_SECTION_DIV   = "-" * 72


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":"))


def load_matrix() -> dict:
    if not os.path.isfile(_MATRIX_PATH):
        sys.exit(f"FATAL: campaign matrix not found at {_MATRIX_PATH}")
    with open(_MATRIX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def report_campaign(c: dict) -> list[str]:
    lines = [
        f"",
        _SECTION_DIV,
        f"  {c['campaign_id']} — {c['name']}",
        _SECTION_DIV,
        f"  Status:           {c['status']}",
        f"  Target gap:       {c['target_gap']}",
        f"  Evidence class:   {c['evidence_class']}",
        f"  Closes stop-ship: {c.get('closes_stop_ship', False)}",
    ]
    if c.get("stop_ship_gate_closed"):
        lines.append(f"  Stop-ship closed: {c['stop_ship_gate_closed']}")

    prereqs = c.get("prerequisites", [])
    if prereqs:
        lines.append(f"  Prerequisites ({len(prereqs)}):")
        for p in prereqs:
            lines.append(f"    - {p}")
    else:
        lines.append(f"  Prerequisites:    None")

    lines.append(f"  Pass condition:   {c['pass_condition'][:80]}{'...' if len(c['pass_condition']) > 80 else ''}")

    closes = c.get("closes_if_pass", [])
    lines.append(f"  Closes if pass:   {', '.join(closes)}")

    remaining = c.get("remains_open", [])
    if remaining:
        lines.append(f"  Remains open:     {', '.join(remaining)}")

    return lines


def build_report(matrix: dict, campaign_filter: str | None = None) -> dict:
    campaigns = matrix.get("campaigns", [])
    if campaign_filter:
        campaigns = [c for c in campaigns if c["campaign_id"] == campaign_filter]
        if not campaigns:
            return {"error": f"Campaign '{campaign_filter}' not found"}

    open_campaigns   = [c for c in campaigns if c["status"] == "OPEN"]
    closed_campaigns = [c for c in campaigns if c["status"] != "OPEN"]
    stop_ship_open   = [g for g in matrix.get("open_stop_ship_gates", []) if g["status"] == "OPEN"]

    return {
        "schema":                   "ph6.evidence_campaign_report.v1",
        "generated_at_utc":         _utc_now(),
        "campaigns_total":          len(campaigns),
        "campaigns_open":           len(open_campaigns),
        "campaigns_closed":         len(closed_campaigns),
        "stop_ship_gates_open":     len(stop_ship_open),
        "production_clearance":     matrix.get("authority_constraints", {}).get("production_clearance_declared", False),
        "local_tooling_status":     matrix.get("local_tooling_status", {}),
        "open_campaigns":           [c["campaign_id"] for c in open_campaigns],
        "open_stop_ship_gates":     [g["id"] for g in stop_ship_open],
        "open_evidence_gaps":       matrix.get("current_open_evidence_gaps", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="PH6 Evidence Campaign Report v1.0")
    parser.add_argument("--campaign", default="", help="Show a single campaign (e.g. EVC-03)")
    parser.add_argument("--json",     action="store_true", help="Machine-readable JSON output")
    args = parser.parse_args()

    matrix = load_matrix()

    if args.json:
        print(_canonical(build_report(matrix, args.campaign or None)))
        return

    report = build_report(matrix, args.campaign or None)
    campaigns = matrix.get("campaigns", [])
    if args.campaign:
        campaigns = [c for c in campaigns if c["campaign_id"] == args.campaign]

    print()
    print(_DIVIDER)
    print("  PH6 EVIDENCE CAMPAIGN REPORT")
    print(_DIVIDER)
    print(f"  Generated:              {report['generated_at_utc']}")
    print(f"  Production clearance:   {report['production_clearance']}")
    print(f"  Campaigns total:        {report['campaigns_total']}")
    print(f"  Campaigns open:         {report['campaigns_open']}")
    print(f"  Campaigns closed:       {report['campaigns_closed']}")
    print(f"  Open stop-ship gates:   {', '.join(report['open_stop_ship_gates']) or 'none'}")
    print()
    print("  LOCAL TOOLING STATUS:")
    for k, v in report.get("local_tooling_status", {}).items():
        print(f"    {k:<35} {v}")
    print()
    print("  OPEN EVIDENCE GAPS:")
    for gap in report.get("open_evidence_gaps", []):
        print(f"    - {gap}")

    for c in campaigns:
        for line in report_campaign(c):
            print(line)

    print()
    print(_DIVIDER)
    print("  NEXT ACTION: Run evidence campaigns in order.")
    print("  Gaps close only with human-reviewed runtime/hardware evidence.")
    print("  Software changes and unit tests cannot substitute.")
    print(_DIVIDER)
    print()


if __name__ == "__main__":
    main()
