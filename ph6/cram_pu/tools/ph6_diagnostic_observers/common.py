"""PH6 Three-Agent Diagnostic -- shared helpers.

Structural isolation: this module and every observer built on it reads existing
JSON/JSONL artifacts with plain stdlib file I/O only. None of them import
CRAMWriter, SheddingLogger.log, evidence_boundary writers, tok.lifecycle's
token-creation entry points, or any other write-capable class. They can
observe records; they cannot produce authoritative ones.

artifact_class: PH6_DIAGNOSTIC_REFERENCE
authority: NONE
authoritative_evidence: false
ratification_status: NONE
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DIAGNOSTIC_AUTHORITY_BLOCK = {
    "artifact_class": "PH6_DIAGNOSTIC_REFERENCE",
    "authority": "NONE",
    "authoritative_evidence": False,
    "ratification_status": "NONE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(path: Path, obj: dict) -> None:
    payload = {**DIAGNOSTIC_AUTHORITY_BLOCK, "lane": obj.pop("lane", "UNSPECIFIED"), **obj}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
