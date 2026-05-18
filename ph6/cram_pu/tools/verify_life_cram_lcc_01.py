#!/usr/bin/env python3
"""
LCC-01 post-run verifier.

Reads a completed LCC-01 run directory and verifies:
  1. Required artifacts present
  2. Camera inventory present and real_source=True
  3. result_set_hash matches recomputed verdict sequence
  4. Replay: re-runs PSEUDO on stored JPEG payloads, compares verdicts
  5. Authority leakage scan pass
  6. RSYNC non-blocking
  7. Minimum frame count (300)

Usage:
    python3 verify_life_cram_lcc_01.py --run-dir <path>

Exit 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))

from ph6.cram_pu.schemas.canonical import canonical_json, blake2b_256, fp_int

BRIGHT_MIN = 20
BRIGHT_MAX = 235
LAP_MIN    = 15.0
MOTION_MAX = 0.40

_FP_BRIGHT_MIN = fp_int(BRIGHT_MIN)
_FP_BRIGHT_MAX = fp_int(BRIGHT_MAX)
_FP_LAP_MIN    = fp_int(LAP_MIN)
_FP_MOTION_MAX = fp_int(MOTION_MAX)

LCC_01A_MIN = 300

REQUIRED_ARTIFACTS = [
    "lcc01_session_manifest.json",
    "lcc01_final_manifest.json",
    "camera_inventory.json",
    "result_set_hash.txt",
    "authority_leakage_scan.json",
    "rsync_observation.json",
    "cram_store/verdict_log.jsonl",
    "cram_store/departure_log.jsonl",
    "cram_store/arrival_log.jsonl",
    "cram_store/shedding_log.jsonl",
    "cram_store/rsync_queue.jsonl",
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _pseudo_metrics_replay(frame: np.ndarray, prev_gray=None) -> dict:
    """Same computation as runner — must match exactly for replay to pass."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mb   = float(np.mean(gray))
    lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        mf   = float(np.mean(diff > 15))
    else:
        mf = 0.0
    return {
        "mean_brightness_fp":  fp_int(mb),
        "laplacian_var_fp":    fp_int(lv),
        "motion_fraction_fp":  fp_int(mf),
    }


def _pseudo_verdict_replay(metrics: dict) -> tuple[str, list[str]]:
    reasons = []
    mb = metrics["mean_brightness_fp"]
    lv = metrics["laplacian_var_fp"]
    mf = metrics["motion_fraction_fp"]
    if mb < _FP_BRIGHT_MIN: reasons.append("brightness_low")
    if mb > _FP_BRIGHT_MAX: reasons.append("brightness_high")
    if lv < _FP_LAP_MIN:    reasons.append("blur_low_detail")
    if mf > _FP_MOTION_MAX: reasons.append("motion_high")
    return ("PASS" if not reasons else "DROP"), reasons


def _decode_jpeg(payload_bytes: bytes) -> np.ndarray | None:
    arr   = np.frombuffer(payload_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame


def check_artifacts(run_dir: Path) -> list[str]:
    missing = []
    for artifact in REQUIRED_ARTIFACTS:
        p = run_dir / artifact
        if not p.exists():
            missing.append(artifact)
    # cram_store must have at least one cram_*.json
    cram_dir = run_dir / "cram_store"
    if cram_dir.exists():
        cram_files = list(cram_dir.glob("cram_*.json"))
        if not cram_files:
            missing.append("cram_store/cram_*.json (no CRAM commits found)")
    return missing


def verify_result_set_hash(run_dir: Path, verdict_records: list) -> tuple[bool, str, str]:
    stored_line = (run_dir / "result_set_hash.txt").read_text().strip()
    stored_hash = stored_line.replace("blake2b256:", "")
    seq = [{"frame_id": r["frame_id"], "verdict": r["verdict"]} for r in verdict_records]
    recomputed = blake2b_256(canonical_json(seq))
    return recomputed == stored_hash, stored_hash, recomputed


def verify_replay(run_dir: Path, verdict_records: list) -> dict:
    payloads_dir = run_dir / "cram_store" / "payloads"
    mismatches: list[dict] = []
    hash_not_found: list[int] = []
    decode_failures: list[int] = []

    prev_gray = None
    for vr in verdict_records:
        frame_id  = vr["frame_id"]
        orig_hash = vr["input_hash"]
        orig_verd = vr["verdict"]

        payload_path = payloads_dir / f"frame_{frame_id:010d}.bin"
        if not payload_path.exists():
            hash_not_found.append(frame_id)
            continue

        payload = payload_path.read_bytes()
        replay_hex  = hashlib.blake2b(payload, digest_size=32).hexdigest()
        replay_hash = "blake2b256:" + replay_hex

        frame = _decode_jpeg(payload)
        if frame is None:
            decode_failures.append(frame_id)
            prev_gray = None
            continue

        metrics = _pseudo_metrics_replay(frame, prev_gray)
        replay_verd, _ = _pseudo_verdict_replay(metrics)
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_gray = gray

        # Normalize prefix — departure_logger stores raw hex; verifier adds "blake2b256:"
        orig_hex = orig_hash.replace("blake2b256:", "")
        if replay_verd != orig_verd or replay_hex != orig_hex:
            mismatches.append({
                "frame_id":        frame_id,
                "original_verdict": orig_verd,
                "replay_verdict":   replay_verd,
                "original_hash":    orig_hash,
                "replay_hash":      replay_hash,
            })

    ok = (len(mismatches) == 0
          and len(hash_not_found) == 0
          and len(decode_failures) == 0)
    return {
        "schema":          "ph6.lcc01_replay_report.v1",
        "timestamp_utc":   _utc(),
        "ok":              ok,
        "total":           len(verdict_records),
        "mismatches":      mismatches,
        "hash_not_found":  hash_not_found,
        "decode_failures": decode_failures,
    }


def verify_cram_chain(run_dir: Path) -> dict:
    cram_dir  = run_dir / "cram_store"
    files     = sorted(cram_dir.glob("cram_*.json"), key=lambda p: p.name)
    chain_ok  = True
    errors: list[str] = []
    prev_hash = "0" * 64

    for p in files:
        rec           = json.loads(p.read_text())
        stored_hash   = rec.get("cram_hash", "")
        stored_prev   = rec.get("prev_cram_hash", "")
        body          = {k: v for k, v in rec.items() if k != "cram_hash"}
        body_bytes    = json.dumps(body, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False, allow_nan=False).encode()
        recomputed    = hashlib.blake2b(body_bytes, digest_size=32).hexdigest()
        if recomputed != stored_hash:
            chain_ok = False
            errors.append(f"{p.name}: hash mismatch")
        if stored_prev != prev_hash:
            chain_ok = False
            errors.append(f"{p.name}: prev_hash mismatch")
        prev_hash = stored_hash

    return {"ok": chain_ok, "total_commits": len(files), "errors": errors}


def run_verify(run_dir: Path) -> dict:
    findings: list[str] = []
    results: dict = {
        "schema":        "ph6.lcc01_verification_report.v1",
        "campaign_id":   "LCC-01",
        "run_dir":       str(run_dir),
        "timestamp_utc": _utc(),
    }

    # 1. Artifacts
    missing = check_artifacts(run_dir)
    results["artifacts_missing"] = missing
    if missing:
        findings.append(f"MISSING ARTIFACTS: {missing}")

    # 2. Camera inventory
    cam_inv_path = run_dir / "camera_inventory.json"
    if cam_inv_path.exists():
        cam_inv = _read_json(cam_inv_path)
        real_source = cam_inv.get("real_source", False)
        results["camera_real_source"] = real_source
        if not real_source:
            findings.append("camera_inventory.real_source != True")
    else:
        results["camera_real_source"] = False
        findings.append("camera_inventory.json missing")

    # 3. Load verdict records
    verdict_log = run_dir / "cram_store" / "verdict_log.jsonl"
    verdict_records = _read_jsonl(verdict_log)
    frames_done = len(verdict_records)
    results["frames_done"] = frames_done

    if frames_done < LCC_01A_MIN:
        findings.append(f"Frame count {frames_done} < minimum {LCC_01A_MIN}")

    # 4. result_set_hash
    try:
        rsh_ok, stored_rsh, recomputed_rsh = verify_result_set_hash(run_dir, verdict_records)
        results["result_set_hash_ok"] = rsh_ok
        results["result_set_hash_stored"]     = stored_rsh
        results["result_set_hash_recomputed"] = recomputed_rsh
        if not rsh_ok:
            findings.append("result_set_hash mismatch: stored != recomputed")
    except Exception as e:
        results["result_set_hash_ok"] = False
        findings.append(f"result_set_hash verify error: {e}")

    # 5. Replay
    print("  Running replay verification...")
    replay = verify_replay(run_dir, verdict_records)
    results["replay"] = replay
    if not replay["ok"]:
        findings.append(
            f"Replay FAIL: mismatches={len(replay['mismatches'])} "
            f"hash_not_found={len(replay['hash_not_found'])} "
            f"decode_failures={len(replay['decode_failures'])}"
        )

    # 6. CRAM chain
    try:
        chain = verify_cram_chain(run_dir)
        results["cram_chain"] = chain
        if not chain["ok"]:
            findings.append(f"CRAM chain FAIL: {chain['errors']}")
    except Exception as e:
        results["cram_chain"] = {"ok": False, "error": str(e)}
        findings.append(f"CRAM chain verify error: {e}")

    # 7. Authority leakage scan
    leak_path = run_dir / "authority_leakage_scan.json"
    if leak_path.exists():
        leak = _read_json(leak_path)
        results["authority_leakage_scan_pass"] = leak.get("scan_pass", False)
        if not leak.get("scan_pass"):
            findings.append("Authority leakage scan FAIL")
    else:
        results["authority_leakage_scan_pass"] = False
        findings.append("authority_leakage_scan.json missing")

    # 8. RSYNC
    rsync_path = run_dir / "rsync_observation.json"
    if rsync_path.exists():
        rsync_obs = _read_json(rsync_path)
        rsync_pass = rsync_obs.get("rsync_pass", False)
        results["rsync_pass"] = rsync_pass
        if not rsync_pass:
            findings.append("RSYNC observation FAIL")
    else:
        results["rsync_pass"] = False
        findings.append("rsync_observation.json missing")

    # Overall
    ok = (
        len(missing) == 0
        and results.get("camera_real_source", False)
        and frames_done >= LCC_01A_MIN
        and results.get("result_set_hash_ok", False)
        and replay["ok"]
        and results.get("cram_chain", {}).get("ok", False)
        and results.get("authority_leakage_scan_pass", False)
        and results.get("rsync_pass", False)
        and len(findings) == 0
    )

    results["findings"]  = findings
    results["ok"]        = ok
    results["verdict"]   = "PASS" if ok else "FAIL"
    results["state"]     = "PASS_PENDING_REVIEW" if ok else "FAIL_EVIDENCE_PRESERVED"
    results["closed"]    = False

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="LCC-01 post-run verifier")
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()

    run_dir = args.run_dir
    if not run_dir.exists():
        print(f"ERROR: run dir not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"LCC-01 Verifier")
    print(f"Run dir: {run_dir}")
    print(f"{'='*70}\n")

    report = run_verify(run_dir)

    # Write report
    report_path = run_dir / "lcc01_verification_report.json"
    tmp = report_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    os.replace(str(tmp), str(report_path))

    print(f"\n{'='*70}")
    print(f"LCC-01 VERIFY: {report['verdict']}")
    print(f"State: {report['state']}  Closed: false")
    print(f"Frames verified: {report['frames_done']}")
    print(f"result_set_hash ok: {report.get('result_set_hash_ok')}")
    print(f"Replay:            {report['replay']['ok']}")
    print(f"CRAM chain:        {report.get('cram_chain', {}).get('ok')}")
    print(f"Leakage scan:      {report.get('authority_leakage_scan_pass')}")
    print(f"RSYNC:             {report.get('rsync_pass')}")
    if report["findings"]:
        print(f"\nFindings:")
        for f in report["findings"]:
            print(f"  - {f}")
    print(f"\nReport: {report_path}")
    print(f"{'='*70}")

    sys.exit(0 if report["ok"] else 1)
