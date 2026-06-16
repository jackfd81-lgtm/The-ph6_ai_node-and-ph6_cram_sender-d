"""
ph6_l2_expand.cli

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (via ph6_l2_expand.mram_s_writer)

Command-line entry point for the SoSo token / virtual-token mapping
subsystem. Default mode is MOCK_OFFLINE_AI; --mode ollama-local is
optional and experimental.

  python3 -m ph6_l2_expand.cli map --source <CRAM_A_OR_R_OBJECT> --out /var/ph6/mram-s/
  python3 -m ph6_l2_expand.cli mock-ai --source <CRAM_A_OR_R_OBJECT> --out /var/ph6/mram-s/
  python3 -m ph6_l2_expand.cli improve --source <CRAM_A_OR_R_OBJECT> --out /var/ph6/mram-s/ --cycles 5
  python3 -m ph6_l2_expand.cli compare-maps --before <MRAM_S_JSON> --after <MRAM_S_JSON>
  python3 -m ph6_l2_expand.cli deepseek --source <CRAM_A_OR_R_OBJECT> --out /var/ph6/mram-s/ --mode mock-offline-ai
  python3 -m ph6_l2_expand.cli deepseek --source <CRAM_A_OR_R_OBJECT> --out /var/ph6/mram-s/ --mode ollama-local
  python3 -m ph6_l2_expand.cli audit --out /var/ph6/mram-s/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ph6_l2_expand.experimental import mock_ai_client
from ph6_l2_expand.experimental.advisory_improvement_tracker import (
    MOCK_OFFLINE_AI,
    OLLAMA_LOCAL,
    build_advisory_record,
    run_cycles,
)
from ph6_l2_expand.mram_s_writer import write_advisory
from ph6_l2_expand.topology_mapper import apply_cycle, deserialize_token_map, serialize_token_map
from ph6_l2_expand.workers import comparison_worker, reference_worker
from ph6_l2_expand.workers.audit_worker import run_audit


def _cmd_map(args: argparse.Namespace) -> int:
    object_id, source_object = reference_worker.load_source(args.source)

    token_map = deserialize_token_map({})
    token_map, metrics, decay_notes, promoted = apply_cycle(
        token_map, object_id, source_object, [], cycle=0,
    )

    advisory_data = {
        "token_map": serialize_token_map(token_map),
        "metrics": metrics,
        "decay_notes": decay_notes,
        "promoted": promoted,
    }
    record = build_advisory_record(object_id, "TOKEN", advisory_data)
    path, status, violations = write_advisory(Path(args.out), f"map_{object_id}.json", record)

    print(json.dumps({"path": str(path), "status": status, "violations": violations, "metrics": metrics}, indent=2))
    return 0


def _cmd_mock_ai(args: argparse.Namespace) -> int:
    object_id, source_object = reference_worker.load_source(args.source)
    advisory = mock_ai_client.generate(object_id, source_object, cycle=1, token_map_before_dict={})
    record = build_advisory_record(object_id, "MOCK_AI", advisory, model_info="mock-offline-ai:deterministic-rule-based")
    path, status, violations = write_advisory(Path(args.out), f"mock_ai_{object_id}.json", record)

    print(json.dumps({"path": str(path), "status": status, "violations": violations, "metrics": advisory["improvement_metrics"]}, indent=2))
    return 0


def _cmd_improve(args: argparse.Namespace) -> int:
    object_id, source_object = reference_worker.load_source(args.source)
    results = run_cycles(object_id, source_object, Path(args.out), args.cycles, mode=MOCK_OFFLINE_AI)
    print(json.dumps({"object_id": object_id, "cycles": results}, indent=2))
    return 0


def _cmd_compare_maps(args: argparse.Namespace) -> int:
    print(json.dumps(comparison_worker.compare(args.before, args.after), indent=2))
    return 0


def _cmd_deepseek(args: argparse.Namespace) -> int:
    object_id, source_object = reference_worker.load_source(args.source)

    if args.mode == OLLAMA_LOCAL:
        from ph6_l2_expand.experimental import deepseek_client
        advisory = deepseek_client.generate(object_id, source_object, cycle=1, token_map_before_dict={})
        model_info = advisory.get("model_info", deepseek_client.DEFAULT_MODEL)
    else:
        advisory = mock_ai_client.generate(object_id, source_object, cycle=1, token_map_before_dict={})
        model_info = "mock-offline-ai:deterministic-rule-based"

    record = build_advisory_record(object_id, "DEEPSEEK", advisory, model_info=model_info)
    mode_slug = args.mode.replace("-", "_")
    path, status, violations = write_advisory(Path(args.out), f"deepseek_{mode_slug}_{object_id}.json", record)

    print(json.dumps({
        "path": str(path),
        "status": status,
        "violations": violations,
        "advisory_status": advisory.get("status", "OK"),
        "metrics": advisory.get("improvement_metrics", {}),
    }, indent=2))
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    report = run_audit(args.out)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "OK" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ph6_l2_expand", description="PH6 Lane-2 SoSo token / virtual-token mapping (Authority ZERO, MRAM-S only)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_map = sub.add_parser("map", help="Build RT tokens from a CRAM-A/R reference object")
    p_map.add_argument("--source", required=True)
    p_map.add_argument("--out", required=True)
    p_map.set_defaults(func=_cmd_map)

    p_mock = sub.add_parser("mock-ai", help="Run one mock AI advisory cycle")
    p_mock.add_argument("--source", required=True)
    p_mock.add_argument("--out", required=True)
    p_mock.set_defaults(func=_cmd_mock_ai)

    p_improve = sub.add_parser("improve", help="Run N advisory improvement cycles")
    p_improve.add_argument("--source", required=True)
    p_improve.add_argument("--out", required=True)
    p_improve.add_argument("--cycles", type=int, default=5)
    p_improve.set_defaults(func=_cmd_improve)

    p_compare = sub.add_parser("compare-maps", help="Compare two MRAM-S advisory records")
    p_compare.add_argument("--before", required=True)
    p_compare.add_argument("--after", required=True)
    p_compare.set_defaults(func=_cmd_compare_maps)

    p_deepseek = sub.add_parser("deepseek", help="Run one DeepSeek (or mock) advisory cycle")
    p_deepseek.add_argument("--source", required=True)
    p_deepseek.add_argument("--out", required=True)
    p_deepseek.add_argument("--mode", choices=[MOCK_OFFLINE_AI, OLLAMA_LOCAL], default=MOCK_OFFLINE_AI)
    p_deepseek.set_defaults(func=_cmd_deepseek)

    p_audit = sub.add_parser("audit", help="Audit an MRAM-S output directory")
    p_audit.add_argument("--out", required=True)
    p_audit.set_defaults(func=_cmd_audit)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
