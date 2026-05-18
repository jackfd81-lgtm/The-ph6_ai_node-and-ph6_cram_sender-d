#!/usr/bin/env python3
"""
EVC-05 — Production-Grade Phased Life CRAM Evidence Campaign

Three sequential 600-frame phases over the shared Life CRAM execution path:
  PHASE_01_FAST       — 600 frames
  PHASE_02_REGULAR    — 600 frames
  PHASE_03_FAST_CRAM  — 600 frames
  Total               — 1800 frames

FAST, REGULAR, and FAST_CRAM are phase labels for EVC-05 over the current
shared Life CRAM execution path. This campaign verifies phased continuity,
artifact completeness, replay parity, RSYNC sovereignty, Lane isolation,
governance capture, and campaign receipt generation. It does not claim
behavioral divergence between modes unless future implementation introduces
mode-specific execution semantics.

Usage:
    python3 run_evc05.py [--device /dev/video0] [--run-dir <path>]
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys
import uuid

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHASES = [
    ("PHASE_01_FAST",      "FAST"),
    ("PHASE_02_REGULAR",   "REGULAR"),
    ("PHASE_03_FAST_CRAM", "FAST_CRAM"),
]
FRAMES_PER_PHASE = 600
TOTAL_FRAMES = FRAMES_PER_PHASE * len(PHASES)

SCRIPT_DIR  = pathlib.Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent.parent.parent
CAMERA_SCRIPT   = SCRIPT_DIR / "life_cram_lcc_01_live_camera.py"
VERIFIER_SCRIPT = SCRIPT_DIR / "verify_life_cram_lcc_01.py"

MODE_NOTE = (
    "FAST, REGULAR, and FAST_CRAM are phase labels for EVC-05 over the "
    "current shared Life CRAM execution path. This campaign verifies phased "
    "continuity, artifact completeness, replay parity, RSYNC sovereignty, "
    "Lane isolation, governance capture, and campaign receipt generation. "
    "It does not claim behavioral divergence between modes unless future "
    "implementation introduces mode-specific execution semantics."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def blake2b256(data: bytes) -> str:
    return "blake2b256:" + hashlib.blake2b(data, digest_size=32).hexdigest()

def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode()

def write_json(path: pathlib.Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

def banner(msg: str) -> None:
    print(f"\n{'='*70}\n{msg}\n{'='*70}")

# ---------------------------------------------------------------------------
# Step 1 — Environment snapshot
# ---------------------------------------------------------------------------

def capture_environment(campaign_dir: pathlib.Path) -> dict:
    env = {"schema": "ph6.evc05.environment_snapshot.v1",
           "captured_utc": now_utc()}

    u = platform.uname()
    env["kernel"]   = f"{u.system} {u.release} {u.machine}"
    env["hostname"] = u.node
    env["python_version"] = sys.version.split("\n")[0]

    def run(cmd):
        try:
            return subprocess.check_output(cmd, stderr=subprocess.DEVNULL,
                                           timeout=10).decode().strip()
        except Exception as e:
            return f"unavailable: {e}"

    env["git_commit"] = run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"])
    env["git_branch"] = run(["git", "-C", str(REPO_ROOT),
                              "rev-parse", "--abbrev-ref", "HEAD"])
    env["disk_state"] = run(["df", "-h"])

    # Storage UUIDs (best-effort, no sudo required for lsblk)
    env["block_devices"] = run(["lsblk", "-o", "NAME,UUID,FSTYPE,SIZE,MOUNTPOINT"])

    # Governance file hashes
    for label, rel in [
        ("governance_closure_hash",
         "PH6_SOURCE/GOVERNANCE/closure_status.json"),
        ("governance_matrix_hash",
         "PH6_SOURCE/GOVERNANCE/evidence_campaign_matrix.json"),
    ]:
        p = REPO_ROOT / rel
        try:
            env[label] = blake2b256(p.read_bytes())
        except Exception as e:
            env[label] = f"ERROR: {e}"

    snap_dir = campaign_dir / "evc05_environment_snapshot"
    snap_dir.mkdir(parents=True, exist_ok=True)
    write_json(snap_dir / "env_capture.json", env)
    print(f"  environment snapshot → {snap_dir}/env_capture.json")
    return env

# ---------------------------------------------------------------------------
# Step 2 — Run one phase
# ---------------------------------------------------------------------------

def run_phase(phase_id: str, phase_label: str,
              campaign_dir: pathlib.Path, device: str) -> pathlib.Path:
    phase_dir = campaign_dir / phase_id.lower()
    phase_dir.mkdir(parents=True, exist_ok=True)

    banner(f"EVC-05 | {phase_id} ({phase_label}) | {FRAMES_PER_PHASE} frames")

    cmd = [
        sys.executable, str(CAMERA_SCRIPT),
        "--frames", str(FRAMES_PER_PHASE),
        "--device", device,
        "--run-dir", str(phase_dir),
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"{phase_id} camera capture failed (rc={result.returncode})")

    return phase_dir

# ---------------------------------------------------------------------------
# Step 3 — Verify one phase
# ---------------------------------------------------------------------------

def verify_phase(phase_dir: pathlib.Path) -> dict:
    cmd = [sys.executable, str(VERIFIER_SCRIPT), "--run-dir", str(phase_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Verifier failed in {phase_dir}")

    # Load structured artifacts
    manifest  = json.loads((phase_dir / "lcc01_final_manifest.json").read_bytes())
    rsync_obs = json.loads((phase_dir / "rsync_observation.json").read_bytes())
    leakage   = json.loads((phase_dir / "authority_leakage_scan.json").read_bytes())

    return {
        "frames_done":        manifest["frames_done"],
        "pass_count":         manifest["pass_count"],
        "drop_count":         manifest["drop_count"],
        "replay_verdict":     manifest["replay_verdict"],
        "schema_ok":          manifest["schema_ok"],
        "leakage_scan_pass":  manifest["leakage_scan_pass"],
        "rsync_pass":         manifest["rsync_pass"],
        "critical_failures":  manifest["critical_failure_count"],
        "result_set_hash":    manifest["result_set_hash"],
        "state":              manifest["state"],
        "actual_fps":         manifest["actual_fps"],
        "rsync_blocked_by":   rsync_obs.get("blocked_by"),
        "lane2_violations":   leakage["lane2_violation_count"],
        "valid_run":          manifest.get("valid_run", True),
    }

# ---------------------------------------------------------------------------
# Step 4 — Per-phase receipt
# ---------------------------------------------------------------------------

def write_phase_receipt(phase_id: str, phase_label: str,
                        phase_dir: pathlib.Path, verified: dict,
                        campaign_dir: pathlib.Path) -> pathlib.Path:
    receipt = {
        "schema": "ph6.evc05.phase_receipt.v1",
        "campaign_id": "EVC-05",
        "phase_id": phase_id,
        "phase_label": phase_label,
        "phase_dir": str(phase_dir),
        "frames_target": FRAMES_PER_PHASE,
        "generated_utc": now_utc(),
        "mode_note": MODE_NOTE,
        **verified,
        "phase_pass": (
            verified["frames_done"] == FRAMES_PER_PHASE and
            verified["replay_verdict"] == "PASS" and
            verified["schema_ok"] and
            verified["leakage_scan_pass"] and
            verified["rsync_pass"] and
            verified["critical_failures"] == 0 and
            verified["lane2_violations"] == 0
        ),
    }

    name_map = {
        "PHASE_01_FAST":      "phase_01_fast_receipt.json",
        "PHASE_02_REGULAR":   "phase_02_regular_receipt.json",
        "PHASE_03_FAST_CRAM": "phase_03_fast_cram_receipt.json",
    }
    out = campaign_dir / name_map[phase_id]
    write_json(out, receipt)
    status = "PASS" if receipt["phase_pass"] else "FAIL"
    print(f"  {phase_id}: {status}  result_set_hash={verified['result_set_hash'][:36]}...")
    return out

# ---------------------------------------------------------------------------
# Step 5 — Campaign-level artifacts
# ---------------------------------------------------------------------------

def write_replay_receipt(phases: list, campaign_dir: pathlib.Path) -> None:
    receipt = {
        "schema": "ph6.evc05.replay_receipt.v1",
        "campaign_id": "EVC-05",
        "generated_utc": now_utc(),
        "phases": [
            {
                "phase_id":       p["phase_id"],
                "phase_label":    p["phase_label"],
                "frames":         p["verified"]["frames_done"],
                "replay_verdict": p["verified"]["replay_verdict"],
                "result_set_hash": p["verified"]["result_set_hash"],
            }
            for p in phases
        ],
        "all_phases_pass": all(
            p["verified"]["replay_verdict"] == "PASS" for p in phases
        ),
        "result_set_hashes_deterministic": len(set(
            p["verified"]["result_set_hash"] for p in phases
        )) == len(phases),
    }
    write_json(campaign_dir / "evc05_replay_receipt.json", receipt)


def write_lane_isolation_report(phases: list, campaign_dir: pathlib.Path) -> None:
    report = {
        "schema": "ph6.evc05.lane_isolation_report.v1",
        "campaign_id": "EVC-05",
        "generated_utc": now_utc(),
        "lane2_authority_rule": "Lane 2 advises. Authority ZERO.",
        "phases": [
            {
                "phase_id":          p["phase_id"],
                "leakage_scan_pass": p["verified"]["leakage_scan_pass"],
                "lane2_violations":  p["verified"]["lane2_violations"],
            }
            for p in phases
        ],
        "total_lane2_violations": sum(
            p["verified"]["lane2_violations"] for p in phases
        ),
        "isolation_pass": all(
            p["verified"]["leakage_scan_pass"] and
            p["verified"]["lane2_violations"] == 0
            for p in phases
        ),
    }
    write_json(campaign_dir / "evc05_lane_isolation_report.json", report)


def write_rsync_report(phases: list, campaign_dir: pathlib.Path) -> None:
    report = {
        "schema": "ph6.evc05.rsync_integrity_report.v1",
        "campaign_id": "EVC-05",
        "generated_utc": now_utc(),
        "rsync_priority": "ZERO — export sovereignty guaranteed",
        "phases": [
            {
                "phase_id":        p["phase_id"],
                "rsync_pass":      p["verified"]["rsync_pass"],
                "rsync_blocked_by": p["verified"]["rsync_blocked_by"],
            }
            for p in phases
        ],
        "any_blocked": any(
            not p["verified"]["rsync_pass"] for p in phases
        ),
        "sovereignty_pass": all(
            p["verified"]["rsync_pass"] for p in phases
        ),
    }
    write_json(campaign_dir / "evc05_rsync_integrity_report.json", report)


def write_governance_snapshot(env: dict, campaign_dir: pathlib.Path) -> None:
    snap = {
        "schema": "ph6.evc05.governance_snapshot.v1",
        "campaign_id": "EVC-05",
        "generated_utc": now_utc(),
        "git_commit": env.get("git_commit"),
        "git_branch": env.get("git_branch"),
        "governance_closure_hash": env.get("governance_closure_hash"),
        "governance_matrix_hash":  env.get("governance_matrix_hash"),
        "python_version": env.get("python_version"),
        "kernel": env.get("kernel"),
        "hostname": env.get("hostname"),
    }
    write_json(campaign_dir / "evc05_governance_snapshot.json", snap)


def write_manifest(phases: list, env: dict, campaign_id: str,
                   campaign_dir: pathlib.Path) -> None:
    manifest = {
        "schema": "ph6.evc05.manifest.v1",
        "campaign_id": "EVC-05",
        "campaign_label": campaign_id,
        "generated_utc": now_utc(),
        "mode_note": MODE_NOTE,
        "frames_per_phase": FRAMES_PER_PHASE,
        "total_frames": TOTAL_FRAMES,
        "phases": [
            {
                "phase_id":        p["phase_id"],
                "phase_label":     p["phase_label"],
                "phase_dir":       p["phase_dir"],
                "frames":          p["verified"]["frames_done"],
                "result_set_hash": p["verified"]["result_set_hash"],
                "phase_pass":      p["receipt_pass"],
            }
            for p in phases
        ],
        "git_commit": env.get("git_commit"),
        "real_source": True,
        "device": phases[0]["device"] if phases else "unknown",
    }
    write_json(campaign_dir / "evc05_manifest.json", manifest)


def compute_campaign_hash(phases: list, campaign_dir: pathlib.Path) -> str:
    # Deterministic: hash of canonical JSON of all phase result_set_hashes
    payload = {
        "campaign_id": "EVC-05",
        "phases": [
            {"phase_id": p["phase_id"], "result_set_hash": p["verified"]["result_set_hash"]}
            for p in phases
        ],
    }
    h = blake2b256(canonical_bytes(payload))
    (campaign_dir / "evc05_result_set_hash.txt").write_text(h + "\n")
    return h


def write_campaign_receipt(phases: list, env: dict, campaign_hash: str,
                           campaign_id: str, all_pass: bool,
                           campaign_dir: pathlib.Path) -> None:
    receipt = {
        "schema": "ph6.evc05.campaign_receipt.v1",
        "campaign_id": "EVC-05",
        "campaign_label": campaign_id,
        "generated_utc": now_utc(),
        "mode_note": MODE_NOTE,
        "reviewer": None,
        "reviewed_at_utc": None,
        "closed": False,
        "state": "PASS_PENDING_REVIEW" if all_pass else "FAIL",
        "production_clearance": "NOT_DECLARED",
        "maximum_automatic_result": "PASS_PENDING_REVIEW",
        "total_frames": TOTAL_FRAMES,
        "frames_per_phase": FRAMES_PER_PHASE,
        "phases_pass": all(p["receipt_pass"] for p in phases),
        "replay_parity": all(
            p["verified"]["replay_verdict"] == "PASS" for p in phases
        ),
        "lane_isolation_pass": all(
            p["verified"]["leakage_scan_pass"] for p in phases
        ),
        "rsync_sovereignty_pass": all(
            p["verified"]["rsync_pass"] for p in phases
        ),
        "campaign_result_set_hash": campaign_hash,
        "git_commit": env.get("git_commit"),
        "phases": [
            {
                "phase_id":        p["phase_id"],
                "phase_label":     p["phase_label"],
                "frames":          p["verified"]["frames_done"],
                "result_set_hash": p["verified"]["result_set_hash"],
                "phase_pass":      p["receipt_pass"],
            }
            for p in phases
        ],
        "required_artifacts": [
            "evc05_manifest.json",
            "evc05_replay_receipt.json",
            "evc05_lane_isolation_report.json",
            "evc05_rsync_integrity_report.json",
            "evc05_governance_snapshot.json",
            "evc05_campaign_receipt.json",
            "evc05_result_set_hash.txt",
            "phase_01_fast_receipt.json",
            "phase_02_regular_receipt.json",
            "phase_03_fast_cram_receipt.json",
        ],
        "all_required_artifacts_present": True,  # set below
    }

    # Verify all named artifacts exist
    missing = [
        a for a in receipt["required_artifacts"]
        if not (campaign_dir / a).exists()
    ]
    receipt["all_required_artifacts_present"] = len(missing) == 0
    receipt["missing_artifacts"] = missing

    receipt["campaign_pass"] = (
        all_pass and
        receipt["all_required_artifacts_present"]
    )

    write_json(campaign_dir / "evc05_campaign_receipt.json", receipt)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EVC-05 phased evidence campaign")
    parser.add_argument("--device",  default="/dev/video0")
    parser.add_argument("--run-dir", default=None)
    args = parser.parse_args()

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    campaign_id = f"evc05_{ts}"
    if args.run_dir:
        campaign_dir = pathlib.Path(args.run_dir)
    else:
        campaign_dir = REPO_ROOT / "ph6/cram_pu/validation_runs" / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)

    banner(f"EVC-05 — Production-Grade Phased Life CRAM Campaign\n"
           f"Run dir : {campaign_dir}\n"
           f"Device  : {args.device}\n"
           f"Phases  : {len(PHASES)} × {FRAMES_PER_PHASE} frames = {TOTAL_FRAMES} total")

    # Environment snapshot
    print("\n[1/7] Capturing environment snapshot...")
    env = capture_environment(campaign_dir)
    print(f"  git_commit: {env.get('git_commit','?')[:16]}...")

    # Run and verify each phase
    phases = []
    for phase_id, phase_label in PHASES:
        phase_dir = run_phase(phase_id, phase_label, campaign_dir, args.device)
        print(f"\n  Verifying {phase_id}...")
        verified = verify_phase(phase_dir)
        receipt_path = write_phase_receipt(phase_id, phase_label, phase_dir,
                                           verified, campaign_dir)
        phases.append({
            "phase_id":    phase_id,
            "phase_label": phase_label,
            "phase_dir":   str(phase_dir),
            "device":      args.device,
            "verified":    verified,
            "receipt_pass": json.loads(receipt_path.read_bytes())["phase_pass"],
        })

    all_pass = all(p["receipt_pass"] for p in phases)

    # Campaign-level artifacts
    banner("EVC-05 | Generating campaign artifacts")
    print("[2/7] Replay receipt...")
    write_replay_receipt(phases, campaign_dir)

    print("[3/7] Lane isolation report...")
    write_lane_isolation_report(phases, campaign_dir)

    print("[4/7] RSYNC sovereignty report...")
    write_rsync_report(phases, campaign_dir)

    print("[5/7] Governance snapshot...")
    write_governance_snapshot(env, campaign_dir)

    print("[6/7] Manifest + result_set_hash...")
    write_manifest(phases, env, campaign_id, campaign_dir)
    campaign_hash = compute_campaign_hash(phases, campaign_dir)
    print(f"  campaign_result_set_hash: {campaign_hash}")

    print("[7/7] Campaign receipt...")
    write_campaign_receipt(phases, env, campaign_hash, campaign_id,
                           all_pass, campaign_dir)

    # Verify all artifacts present
    required = [
        "evc05_manifest.json", "evc05_replay_receipt.json",
        "evc05_lane_isolation_report.json", "evc05_rsync_integrity_report.json",
        "evc05_governance_snapshot.json", "evc05_campaign_receipt.json",
        "evc05_result_set_hash.txt",
        "phase_01_fast_receipt.json", "phase_02_regular_receipt.json",
        "phase_03_fast_cram_receipt.json",
    ]
    missing = [a for a in required if not (campaign_dir / a).exists()]

    banner("EVC-05 RESULT")
    total_frames = sum(p["verified"]["frames_done"] for p in phases)
    print(f"Total frames    : {total_frames} / {TOTAL_FRAMES}")
    for p in phases:
        v = p["verified"]
        status = "PASS" if p["receipt_pass"] else "FAIL"
        print(f"  {p['phase_id']:25s}: {status}  "
              f"frames={v['frames_done']}  fps={v['actual_fps']:.1f}  "
              f"drop={v['drop_count']}  lane2_viol={v['lane2_violations']}")
    print(f"Replay parity   : {'PASS' if all(p['verified']['replay_verdict']=='PASS' for p in phases) else 'FAIL'}")
    print(f"Lane isolation  : {'PASS' if all(p['verified']['leakage_scan_pass'] for p in phases) else 'FAIL'}")
    print(f"RSYNC sovereign : {'PASS' if all(p['verified']['rsync_pass'] for p in phases) else 'FAIL'}")
    print(f"All artifacts   : {'PASS' if not missing else 'FAIL  missing=' + str(missing)}")
    print(f"Campaign hash   : {campaign_hash}")
    print(f"Run dir         : {campaign_dir}")
    print(f"\nEVC-05 CAMPAIGN : {'PASS' if all_pass and not missing else 'FAIL'}")
    print(f"State           : {'PASS_PENDING_REVIEW' if all_pass else 'FAIL'}")
    print(f"Closed          : false")
    print(f"Production      : NOT_DECLARED")

    return 0 if (all_pass and not missing) else 1


if __name__ == "__main__":
    sys.exit(main())
