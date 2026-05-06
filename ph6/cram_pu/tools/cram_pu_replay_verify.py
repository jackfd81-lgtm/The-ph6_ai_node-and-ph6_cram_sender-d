"""
Phase 8 — CRAM-PU replay verifier.
Re-runs PSEUDO metrics from the original payload bytes using only the
stored input_hash as the key. Proves determinism:
  same input hash → same metrics → same verdict
SoSo advisory state is NOT used in replay — advisory independence guaranteed.
Writes replay_report.json.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np


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


def _read_cram_commits(cram_dir: Path) -> list:
    files = sorted(cram_dir.glob("cram_*.json"))
    commits = []
    for p in files:
        with p.open("r", encoding="utf-8") as f:
            commits.append(json.load(f))
    return commits


def _blake2b256_bytes(data: bytes) -> str:
    return "blake2b256:" + hashlib.blake2b(data, digest_size=32).hexdigest()


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _blake2b256_obj(obj: dict) -> str:
    return hashlib.blake2b(_canonical_bytes(obj), digest_size=32).hexdigest()


def _decode_frame(payload: bytes) -> np.ndarray:
    arr = np.frombuffer(payload, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        side = max(1, int(len(payload) ** 0.5))
        gray_bytes = payload[:side * side]
        if len(gray_bytes) < side * side:
            gray_bytes = gray_bytes.ljust(side * side, b'\x80')
        frame = np.frombuffer(gray_bytes, dtype=np.uint8).reshape(side, side)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    return frame


BRIGHT_MIN  = 20
BRIGHT_MAX  = 235
LAP_MIN     = 15.0
MOTION_MAX  = 0.40


def _pseudo_metrics(frame: np.ndarray, prev_gray=None) -> dict:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mb   = float(np.mean(gray))
    lv   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        mf   = float(np.mean(diff > 15))
    else:
        mf   = 0.0
    return {"mean_brightness": round(mb, 4),
            "laplacian_var":   round(lv, 4),
            "motion_fraction": round(mf, 4)}


def _pseudo_verdict(metrics: dict) -> tuple:
    reasons = []
    if metrics["mean_brightness"] < BRIGHT_MIN: reasons.append("brightness_low")
    if metrics["mean_brightness"] > BRIGHT_MAX: reasons.append("brightness_high")
    if metrics["laplacian_var"]   < LAP_MIN:    reasons.append("blur_low_detail")
    if metrics["motion_fraction"] > MOTION_MAX: reasons.append("motion_high")
    return ("PASS" if not reasons else "DROP"), reasons


def verify_replay(original_verdicts: list, payloads: dict,
                  cram_dir: Path, report_path: Path) -> dict:
    """
    For each original verdict, re-run PSEUDO on the same payload (keyed by
    input_hash). Check that replay verdict == original verdict.
    Also verify CRAM chain integrity.
    """
    # Build hash → payload lookup
    hash_to_payload = {}
    for pid, payload in payloads.items():
        h = _blake2b256_bytes(payload)
        hash_to_payload[h] = payload

    mismatches = []
    hash_not_found = []
    replay_results = []
    prev_gray = None

    for orig in original_verdicts:
        input_hash = orig["input_hash"]
        payload = hash_to_payload.get(input_hash)
        if payload is None:
            hash_not_found.append({"packet_id": orig["packet_id"], "input_hash": input_hash})
            continue

        frame   = _decode_frame(payload)
        metrics = _pseudo_metrics(frame, prev_gray)
        verdict, reasons = _pseudo_verdict(metrics)
        prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        replay_input_hash = _blake2b256_bytes(payload)

        match = (
            verdict == orig["verdict"]
            and replay_input_hash == orig["input_hash"]
        )
        if not match:
            mismatches.append({
                "packet_id":       orig["packet_id"],
                "original_verdict": orig["verdict"],
                "replay_verdict":   verdict,
                "original_hash":    orig["input_hash"],
                "replay_hash":      replay_input_hash,
            })
        replay_results.append({
            "packet_id":      orig["packet_id"],
            "input_hash":     replay_input_hash,
            "replay_verdict": verdict,
            "match":          match,
        })

    # CRAM chain integrity
    commits      = _read_cram_commits(cram_dir)
    chain_valid  = True
    prev_hash    = "0" * 64
    chain_errors = []

    for commit in commits:
        stored_hash = commit.get("cram_hash", "")
        stored_prev = commit.get("prev_cram_hash", "")
        body = {k: v for k, v in commit.items() if k != "cram_hash"}
        recomputed = _blake2b256_obj(body)
        if stored_prev != prev_hash or recomputed != stored_hash:
            chain_valid = False
            chain_errors.append(commit.get("commit_seq"))
        prev_hash = stored_hash

    ok = (
        len(mismatches) == 0
        and len(hash_not_found) == 0
        and chain_valid
    )

    report = {
        "schema":          "ph6.replay_report.v1",
        "timestamp":       time.time(),
        "ok":              ok,
        "total":           len(original_verdicts),
        "replayed":        len(replay_results),
        "mismatches":      mismatches,
        "hash_not_found":  hash_not_found,
        "chain_valid":     chain_valid,
        "chain_errors":    chain_errors,
        "cram_commits":    len(commits),
        "soso_used":       False,  # advisory never replayed
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = report_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True,
                               ensure_ascii=False, allow_nan=False))
    os.replace(str(tmp), str(report_path))

    return report


if __name__ == "__main__":
    import argparse, base64
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict-log",   required=True)
    ap.add_argument("--payloads-json", required=True)
    ap.add_argument("--cram-dir",      required=True)
    ap.add_argument("--report",        required=True)
    args = ap.parse_args()

    with Path(args.verdict_log).open() as f:
        verdicts = [json.loads(l) for l in f if l.strip()]
    raw = json.loads(Path(args.payloads_json).read_text())
    payloads = {k: base64.b64decode(v) for k, v in raw.items()}
    report = verify_replay(verdicts, payloads, Path(args.cram_dir), Path(args.report))
    status = "PASS" if report["ok"] else "FAIL"
    print(f"REPLAY: {status}  replayed={report['replayed']}  "
          f"mismatches={len(report['mismatches'])}  chain_valid={report['chain_valid']}")
    sys.exit(0 if report["ok"] else 1)
