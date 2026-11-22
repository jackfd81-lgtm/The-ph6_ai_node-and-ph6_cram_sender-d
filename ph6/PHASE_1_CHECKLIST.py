#!/usr/bin/env python3
"""
PH6 PHASE 1: MINIMAL LOOP EXECUTION CHECKLIST

Goal: USB Camera → FAST Capture → PSEUDO-M → PSEUDO-A → CRAM-A/R → Replay

Nothing else.

This week:
  1. Clean 12,000-frame baseline package
  2. Make loop run continuously
  3. Convert to systemd services
  4. Build recovery checks
  5. Build ph6_cert.py
  6. Run 12,000-frame validation
  7. Add Zero 2W sentinel

At week end: Operational deterministic core.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import List


class Status(str, Enum):
    TODO        = "⬜ TODO"
    IN_PROGRESS = "🔄 IN_PROGRESS"
    DONE        = "✅ DONE"
    BLOCKED     = "🔴 BLOCKED"


@dataclass
class Checkpoint:
    day: int
    task: str
    component: str
    status: Status
    definition: str
    test_command: str
    blocking: bool
    estimated_time: str


PHASE_1_CHECKLIST = [
    # DAY 1: BASELINE HYGIENE
    Checkpoint(
        day=1,
        task="Clean 12,000-frame baseline",
        component="Input",
        status=Status.TODO,
        definition="""
        1. Inventory existing baseline package
           - Verify frame count: 12,000
           - Check timestamp consistency
           - Verify SHA256 hashes intact

        2. Extract summary stats
           - Frame min/max/mean brightness
           - Entropy distribution
           - Motion fraction range
           - Blur variance range

        3. Verify determinism
           - Re-measure 100 frames from baseline
           - Confirm PSEUDO-M output matches original
           - Log any variance (should be zero)

        4. Document baseline
           - Save summary.json with stats
           - Save baseline.manifest with hashes
           - Save measurement.log with full audit trail
        """,
        test_command="python3 ph6/cram_pu/ph6_internal_test.py",
        blocking=True,
        estimated_time="2h",
    ),

    # DAY 2: CAPTURE LOOP
    Checkpoint(
        day=2,
        task="Make USB camera loop continuous",
        component="FAST Capture",
        status=Status.TODO,
        definition="""
        1. Implement capture_loop.py
           - Read USB camera at 25 fps
           - Assign sequence number (start: 0)
           - Assign timestamp (system clock)
           - Queue frame for PSEUDO-M

        2. Never block downstream
           - If PSEUDO-M is slow, drop frame
           - Log drops with reason
           - Keep stats: captured, processed, dropped

        3. Run for 10 minutes
           - Capture ~15,000 frames
           - Zero crashes
           - Zero lock-ups

        4. Measure:
           - FPS actual vs target
           - Drop rate
           - Memory footprint
           - CPU usage
        """,
        test_command="python3 PH6_SOURCE/TESTS/USB_CAMERA_12000/run_usb_camera_12000.py --frames 500 --width 1280 --height 720 --fps 25",
        blocking=True,
        estimated_time="3h",
    ),

    Checkpoint(
        day=2,
        task="Make PSEUDO-M deterministic",
        component="PSEUDO Measurement",
        status=Status.DONE,
        definition="""
        1. pseudo_measure.py is deterministic
           - Same frame → same output always
           - No floating-point variance
           - No randomness in calculations

        2. Stage 3 (2026-06-01) confirmed:
           - 12,000 frames measured
           - Replay chain: MATCH
           - _BLUR_DROP_LOW calibrated to 0.3 for MJPEG

        3. BLAKE2b-256 anchor verified:
           014652358db408cf7977c3e99ab3cceb57ee01d7bf7c265daaaead625485a2d7
        """,
        test_command="python3 ph6/cram_pu/ph6_internal_test.py",
        blocking=True,
        estimated_time="DONE",
    ),

    # DAY 3: AUTHORITY + STORAGE
    Checkpoint(
        day=3,
        task="Authority issues PASS/DROP only",
        component="PSEUDO Authority",
        status=Status.DONE,
        definition="""
        1. pseudo_authority.py reads measurements
           - One input: measurement dict
           - Two outputs: PASS or DROP (nothing else)
           - No third option

        2. Thresholds (ratified 2026-06-01):
           - _BLUR_DROP_LOW = 0.3 (MJPEG 1280x720)
           - _LUMA_BLACK_MAX = 3.0
           - _LUMA_WHITE_MIN = 252.0

        3. Verdict immutable
           - Once issued, cannot change
           - Logged immediately
           - No override possible

        4. Stage 3 results (ratified):
           LIGHT: 3000 PASS, 0 DROP
           DARKNESS: 2982 PASS, 18 DROP
           MOVEMENT: 2994 PASS, 6 DROP
           FOCUS: 3000 PASS, 0 DROP
        """,
        test_command="python3 PH6_SOURCE/TESTS/USB_CAMERA_12000/run_usb_camera_12000.py --frames 1000 --width 1280 --height 720",
        blocking=True,
        estimated_time="DONE",
    ),

    Checkpoint(
        day=3,
        task="CRAM-A stores PASS, CRAM-R stores DROP",
        component="SLOW CRAM",
        status=Status.TODO,
        definition="""
        1. cram_writer.py creates CRAM-A records
           - Input: frame + measurements + PASS verdict
           - Atomic write (all-or-nothing)
           - fsync after every write
           - BLAKE2b-256 hash
           - SHA-256 payload hash

        2. reject_writer.py creates CRAM-R records
           - Input: frame + measurements + DROP reason
           - Atomic write
           - fsync after every write
           - Preserved DROP evidence

        3. Crash safety test
           - Write 1000 frames to CRAM-A
           - Kill process mid-write
           - Verify recovery: no partial records
           - Verify all completed records intact

        4. Hash verification
           - Read back all CRAM-A records
           - Verify BLAKE2b matches
           - 100% match required
        """,
        test_command="python3 ph6/cram_pu/ph6_cram_sim.py",
        blocking=True,
        estimated_time="3h",
    ),

    # DAY 4: REPLAY
    Checkpoint(
        day=4,
        task="Replay proves determinism",
        component="Replay Verification",
        status=Status.DONE,
        definition="""
        1. replay_compare.py reads CRAM run artifacts
           - Reads pseudo_measurements.jsonl
           - Reads pseudo_verdicts.jsonl
           - Reads replay_digest.json

        2. Verifies hash chain
           - Computes chain_digest from measurement hashes
           - Computes summary_digest from counts + chain
           - Compares against stored digest

        3. Stage 3 replay (ratified 2026-06-01):
           - Status: MATCH
           - Digest: a6813ebc1c7c9a20e80883c95058610f26094faa187668eceee24e87bf56b757
           - Frames: 12,000
        """,
        test_command="python3 PH6_SOURCE/TESTS/USB_CAMERA_12000/replay_compare.py ph6/cram_pu/validation_runs/STAGE3_20260601T121410Z/",
        blocking=True,
        estimated_time="DONE",
    ),

    Checkpoint(
        day=4,
        task="Full loop integration test",
        component="Integration",
        status=Status.TODO,
        definition="""
        1. Run complete flow:
           USB Camera → run_usb_camera_12000.py
           Output: pseudo_measurements.jsonl + replay_digest.json

        2. Verify:
           - Capture: seq numbers consecutive
           - PSEUDO-M: measurements deterministic
           - PSEUDO-A: verdicts consistent
           - Replay: MATCH on all

        3. Run python3 ph6/ph6_cert.py --standard
           Must return PASS.
        """,
        test_command="python3 ph6/ph6_cert.py --standard",
        blocking=True,
        estimated_time="1h",
    ),

    # DAY 5: SYSTEMD SERVICES
    Checkpoint(
        day=5,
        task="Review and optionally enable systemd services",
        component="Operationalization",
        status=Status.TODO,
        definition="""
        1. Review service templates:
           ph6/systemd_service_templates/ph6-capture.service
           ph6/systemd_service_templates/ph6-pseudo.service
           ph6/systemd_service_templates/ph6-cram.service
           ph6/systemd_service_templates/ph6-replay.service
           ph6/systemd_service_templates/ph6-replay.timer
           ph6/systemd_service_templates/ph6-recovery.service

        2. These reference /opt/ph6/ — deployment target.
           DO NOT enable until code is staged there.

        3. Operator decision required before enabling.

        4. Start order:
           ph6-recovery (boot check)
           → ph6-capture
           → ph6-pseudo (after capture)
           → ph6-cram (after pseudo)
           → ph6-replay (timer, hourly)
        """,
        test_command="ls ph6/systemd_service_templates/",
        blocking=False,
        estimated_time="2h",
    ),

    # DAY 5-6: RECOVERY
    Checkpoint(
        day=6,
        task="Build recovery checks",
        component="Resilience",
        status=Status.TODO,
        definition="""
        1. Power loss simulation
           - Run loop for 5 minutes
           - Kill process hard
           - Restart
           - Verify last completed record intact

        2. Reboot test
           - Run loop for 5 minutes
           - Clean reboot
           - Verify capture resumes with correct seq number

        3. Recovery check
           - Verify CRAM integrity on restart
           - Check for orphaned records
           - Log recovery events
        """,
        test_command="python3 ph6/cram_pu/ph6_internal_test.py",
        blocking=True,
        estimated_time="2h",
    ),

    # DAY 6: CERTIFICATION HARNESS
    Checkpoint(
        day=6,
        task="Certification harness (ph6_cert.py)",
        component="Testing",
        status=Status.TODO,
        definition="""
        Three levels:
          --smoke    500 frames,   ~2 min
          --standard 3000 frames, ~10 min
          --full     12000 frames, ~8 min

        Each checks:
          1. Anchor hash (ph6_internal_test.py)
          2. Camera capture (0 failures)
          3. PASS rate (> 90%)
          4. Replay (MATCH)

        Output: PASS or FAIL + JSON report
        """,
        test_command="python3 ph6/ph6_cert.py --smoke",
        blocking=False,
        estimated_time="1h",
    ),

    # DAY 7: VALIDATION
    Checkpoint(
        day=7,
        task="Run 12,000-frame full certification",
        component="Validation",
        status=Status.TODO,
        definition="""
        Final Phase 1 gate:
          python3 ph6/ph6_cert.py --full

        Must return PASS with:
          - Anchor: PASS
          - Frames: 12,000, 0 failures
          - PASS rate: > 90%
          - Replay: MATCH
          - Thermal: < 70°C
        """,
        test_command="python3 ph6/ph6_cert.py --full",
        blocking=True,
        estimated_time="1h",
    ),

    # DAY 7: ZERO SENTINEL
    Checkpoint(
        day=7,
        task="Zero 2W sentinel monitoring",
        component="Multi-node",
        status=Status.TODO,
        definition="""
        Zero 2W (192.168.254.189 / jackjack2):
          - SSH access to main Pi
          - Verify CRAM artifacts present
          - Check last frame timestamp
          - Alert if > 2 min without new frame
          - Log to sentinel.log

        Operator note: Zero 2W = SSH only, no Claude.
        """,
        test_command="ssh 192.168.254.189 'uptime'",
        blocking=False,
        estimated_time="2h",
    ),
]


def print_checklist() -> None:
    print("\n" + "=" * 80)
    print("PHASE 1: MINIMAL LOOP — WEEKLY EXECUTION CHECKLIST")
    print("=" * 80)
    print("\nGoal: Prove deterministic core works. Chain verified end-to-end.\n")

    current_day = 0
    for cp in PHASE_1_CHECKLIST:
        if cp.day != current_day:
            current_day = cp.day
            day_name = {1: "Monday", 2: "Tuesday", 3: "Wednesday",
                        4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}.get(cp.day, f"Day {cp.day}")
            print(f"\n{'─' * 80}")
            print(f"DAY {cp.day} ({day_name})")
            print(f"{'─' * 80}\n")

        print(f"{cp.status.value}  {cp.task}")
        print(f"   Component: {cp.component}   Time: {cp.estimated_time}")
        if cp.blocking:
            print(f"   🔴 BLOCKING — must pass before proceeding")
        for line in cp.definition.strip().split("\n"):
            print(f"   {line}")
        print(f"\n   Test: {cp.test_command}\n")

    done  = sum(1 for c in PHASE_1_CHECKLIST if c.status == Status.DONE)
    total = len(PHASE_1_CHECKLIST)
    pct   = int(100 * done / total)

    print("=" * 80)
    print(f"PHASE 1 PROGRESS: {done}/{total} checkpoints DONE ({pct}%)")
    print("=" * 80)
    print("""
CRITICAL PATH (cannot skip):
  ✓ Anchor hash verified
  ✓ PSEUDO-M deterministic (Stage 3 ratified)
  ✓ PSEUDO-A PASS/DROP immutable (Stage 3 ratified)
  ✓ Replay MATCH (Stage 3 ratified)
  ○ CRAM-A/R crash-safe storage
  ○ Full loop integration
  ○ Systemd services (operator decision)
  ○ Recovery from power loss
  ○ 12,000-frame cert → PASS

AT WEEK END:
  python3 ph6/ph6_cert.py --full → PASS

  You have a deterministic core that:
  - Captures continuously
  - Measures deterministically
  - Issues verdicts immutably
  - Replays with MATCH
  - Boots automatically
""")


if __name__ == "__main__":
    print_checklist()
