"""
ph6.cram_pu.vrc — Validator Replay Certification v1.0 (PH6-VRC-1.0)

Certifies that replay output is consistent with the ingest receipt chain.

VRC-1.0 DOES:
  - walk the ingest receipt log for INGEST_ACCEPTED events
  - locate the corresponding CRAM commit file for each accepted frame
  - verify that the CRAM file's cram_hash matches the receipt's authority_hash
  - verify the CRAM hash chain is intact (prev_cram_hash linkage)
  - emit a structured certification receipt (ph6.vrc_receipt.v1)

VRC-1.0 DOES NOT:
  - declare production clearance (OI-01 and OI-03 remain open)
  - issue PASS/DROP
  - repair broken chains
  - suppress failures
  - override runtime evidence

Authority: VERIFY ONLY (CVS-3 layer)
Schema:    ph6.vrc_receipt.v1
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ph6.cfc import make_failure, make_replay_failure
from ph6.cram_pu.ingest_receipt_verify import verify_receipt_chain


_RECEIPT_LOG = "ingest_receipt_log.jsonl"
_GENESIS     = "0" * 64


def _blake2b(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(",", ":"),
    ).encode("utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_cram_file(store: Path, frame_id_str: str) -> dict | None:
    """Load cram_<frame_id:010d>.json from the CRAM store."""
    try:
        fid = int(frame_id_str.replace("frame_", ""))
        path = store / f"cram_{fid:010d}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError, json.JSONDecodeError):
        return None


def _read_accepted_receipts(log_path: Path) -> list[dict]:
    """Return all INGEST_ACCEPTED receipts in event_seq order."""
    if not log_path.exists():
        return []
    results = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                r = json.loads(stripped)
                if r.get("event_type") == "INGEST_ACCEPTED":
                    results.append(r)
            except json.JSONDecodeError:
                pass
    return sorted(results, key=lambda r: r.get("event_seq", 0))


# ── Certification steps ───────────────────────────────────────────────────────

def step_a_receipt_chain_intact(store: Path, now: str) -> tuple[bool, list[dict]]:
    """Step A: Verify the ingest receipt chain is intact."""
    log_path = store / _RECEIPT_LOG
    report = verify_receipt_chain(log_path)
    failures = []
    if not report["chain_intact"]:
        for f in report.get("findings", []):
            if f.get("severity") in ("HIGH", "CRITICAL"):
                failures.append(make_failure(
                    f.get("violation_class", "R4"), "HIGH",
                    f"Ingest receipt chain integrity failure: {f.get('reason', '')}",
                    line=f.get("line"), timestamp_utc=now,
                ))
    return report["chain_intact"], failures


def step_b_accepted_frames_have_cram(
    store: Path, now: str
) -> tuple[int, int, list[dict]]:
    """
    Step B: Every INGEST_ACCEPTED receipt must have a corresponding CRAM file.
    Returns (verified_count, missing_count, failures).
    """
    accepted = _read_accepted_receipts(store / _RECEIPT_LOG)
    verified = 0
    failures = []

    for receipt in accepted:
        obj_id = receipt.get("object_id", "?")
        cram = _load_cram_file(store, obj_id)

        if cram is None:
            failures.append(make_replay_failure(
                "R5", "CRITICAL",
                "INGEST_ACCEPTED receipt has no corresponding CRAM commit file",
                object_id=obj_id, timestamp_utc=now,
            ))
            continue

        # Check authority_hash matches cram_hash
        receipt_authority = receipt.get("authority_hash")
        cram_hash = cram.get("cram_hash")

        if receipt_authority != cram_hash:
            failures.append(make_replay_failure(
                "R3", "HIGH",
                "authority_hash in ingest receipt does not match cram_hash in CRAM file",
                object_id=obj_id,
                expected_hash=receipt_authority,
                observed_hash=cram_hash,
                timestamp_utc=now,
            ))
            continue

        verified += 1

    return verified, len(accepted) - verified, failures


def step_c_cram_hash_chain(store: Path, now: str) -> tuple[bool, list[dict]]:
    """
    Step C: Verify the CRAM hash chain (prev_cram_hash linkage).
    Walks all cram_*.json files in frame_id order.
    """
    cram_files = sorted(store.glob("cram_*.json"), key=lambda p: p.name)
    failures = []
    prev_hash = _GENESIS

    for path in cram_files:
        try:
            with path.open("r", encoding="utf-8") as f:
                rec = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            failures.append(make_failure(
                "C1", "HIGH", f"CRAM file unreadable: {e}",
                file=str(path), timestamp_utc=now,
            ))
            continue

        stored_hash = rec.get("cram_hash", "")
        stored_prev = rec.get("prev_cram_hash", "")
        frame_id    = rec.get("frame_id")

        # Verify stored cram_hash matches recomputed hash
        body = {k: v for k, v in rec.items() if k != "cram_hash"}
        recomputed = _blake2b(_canonical(body))
        if recomputed != stored_hash:
            failures.append(make_replay_failure(
                "R3", "HIGH",
                "CRAM file cram_hash mismatch — content corrupted",
                object_id=str(path.name),
                expected_hash=recomputed,
                observed_hash=stored_hash,
                timestamp_utc=now,
            ))

        # Verify chain linkage
        if stored_prev != prev_hash:
            failures.append(make_replay_failure(
                "R4", "HIGH",
                "CRAM prev_cram_hash chain break",
                object_id=str(path.name),
                expected_hash=prev_hash,
                observed_hash=stored_prev,
                timestamp_utc=now,
            ))

        prev_hash = stored_hash

    return len(failures) == 0, failures


# ── Main certification runner ─────────────────────────────────────────────────

def certify(store: Path) -> dict:
    """
    Run VRC-1.0 certification against a CRAM store.

    Returns a ph6.vrc_receipt.v1 dict. The caller must write it to disk
    if a permanent record is needed.

    This receipt does NOT constitute production clearance.
    OI-01 and OI-03 remain open STOP-SHIP gates.
    """
    now            = _utc_now()
    cert_id        = f"vrc-{secrets.token_hex(8)}"
    all_failures   = []

    chain_intact, fa = step_a_receipt_chain_intact(store, now)
    all_failures.extend(fa)

    verified, missing, fb = step_b_accepted_frames_have_cram(store, now)
    all_failures.extend(fb)

    cram_chain_ok, fc = step_c_cram_hash_chain(store, now)
    all_failures.extend(fc)

    passed = len(all_failures) == 0

    receipt: dict[str, Any] = {
        "schema":                 "ph6.vrc_receipt.v1",
        "cert_id":                cert_id,
        "authority":              "VERIFY_ONLY",
        "production_clearance":   False,
        "production_clearance_note": (
            "VRC-1.0 certifies replay consistency only. "
            "Production clearance requires OI-01 and OI-03 hardware evidence."
        ),
        "passed":                 passed,
        "failure_count":          len(all_failures),
        "steps": {
            "A_receipt_chain_intact":    chain_intact,
            "B_accepted_frames_in_cram": verified,
            "B_accepted_frames_missing": missing,
            "C_cram_chain_intact":       cram_chain_ok,
        },
        "failures":               all_failures,
        "cram_store":             str(store),
        "open_stop_ship_gates":   ["OI-01", "OI-03"],
        "timestamp_utc":          now,
    }

    # Seal the receipt
    body = {k: v for k, v in receipt.items() if k != "cert_hash"}
    receipt["cert_hash"] = _blake2b(_canonical(body))

    return receipt
