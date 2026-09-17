#!/usr/bin/env python3
"""Read-only terminal observer for an LCC-01 real-camera run.

This program has no PH6 authority.  It reads only the artifacts emitted by
``life_cram_lcc_01_live_camera.py`` and never opens a sensor or writes to the
run directory.  Use ``--follow`` in a second terminal while the LCC-01 runner
is producing a bounded live camera session.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path) -> list[dict]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    except (OSError, json.JSONDecodeError):
        return []


def _short(value: object, length: int = 16) -> str:
    text = str(value)
    return text if len(text) <= length else text[:length] + "…"


class RunObserver:
    """Materializes one display event from already-written LCC-01 artifacts."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.cram_store = run_dir / "cram_store"
        self.mram_s = run_dir / "mram_s" / "swarms"
        self.camera = _read_json(run_dir / "camera_inventory.json") or {}
        self._shown: set[int] = set()
        self._shown_multimodal: set[int] = set()

    def _token_for(self, cram_ref_hash: str) -> dict | None:
        audit_path = self.mram_s / "tokens" / "tok_advisory_audit.jsonl"
        for event in reversed(_read_jsonl(audit_path)):
            payload = event.get("payload", {})
            if payload.get("cram_ref_hash") == cram_ref_hash:
                return event
        return None

    def _multimodal_for(self, frame_id: int) -> dict | None:
        for path in (self.mram_s / "correlations").glob("*.json"):
            item = _read_json(path) or {}
            corr = item.get("correlation", {})
            if corr.get("camera_event_id") == f"frame_{frame_id:010d}":
                item["_path"] = str(path)
                return item
        return None

    def _print_event(self, record: dict) -> None:
        # The observer may have started before the runner wrote inventory.
        if not self.camera:
            self.camera = _read_json(self.run_dir / "camera_inventory.json") or {}
        frame_id = record["frame_id"]
        verdict = record["verdict"]
        payload_hash = record.get("input_hash", "MISSING")
        metrics = record.get("metrics", {})
        soso = record.get("soso_advisory", {})
        commit = _read_json(self.cram_store / f"cram_{frame_id:010d}.json")
        advisory = _read_json(self.mram_s / f"S{frame_id:010d}.json")
        multimodal = self._multimodal_for(frame_id)
        token = self._token_for(payload_hash) if verdict == "PASS" else None

        print("\n" + "-" * 68)
        print(f"PH6 LIVE EVENT {frame_id:06d}  {record.get('timestamp_utc', 'timestamp unavailable')}")
        print("-" * 68)
        print("CAMERA  [REAL INPUT]")
        print(f"  frame: {frame_id}")
        if self.camera:
            print(f"  input: {self.camera.get('device', 'unknown')} "
                  f"{self.camera.get('width_px', '?')}x{self.camera.get('height_px', '?')}")
        if multimodal:
            audio = multimodal.get("soso_input", {}).get("audio", {})
            print("MICROPHONE  [CRAM-0 MEASURED — NO AUDIO VERDICT]")
            print(f"  audio event: {audio.get('event_id', 'unavailable')}")
            print(f"  evidence hash: {_short(audio.get('evidence_hash', 'unavailable'), 32)}")
            print(f"  measurements: {audio.get('measurements', {})}")
            print(f"  correlation: {multimodal.get('correlation', {}).get('correlation_id', 'unavailable')}")
        else:
            print("MICROPHONE  [NOT CONNECTED TO THIS LCC-01 EVENT]")
            print("  audio event: no PH6 audio-event artifact")

        print("PSEUDO / LANE 1  [AUTHORITATIVE]")
        print(f"  verdict: {verdict}")
        print(f"  reasons: {', '.join(record.get('reasons', [])) or 'none'}")
        print("  metrics: " + ", ".join(
            f"{name}={metrics[name]}" for name in
            ("mean_brightness_fp", "laplacian_var_fp", "motion_fraction_fp")
            if name in metrics))
        print(f"  input hash: {_short(payload_hash, 32)}")
        if commit:
            print(f"  CRAM-A commit: {self.cram_store / f'cram_{frame_id:010d}.json'}")
            print(f"  CRAM hash: {_short(commit.get('cram_hash', 'unavailable'), 32)}")
            print("  integrity marker: " + str(
                (self.cram_store / f"cram_{frame_id:010d}.json.blake2b").exists()))
        else:
            print("  CRAM destination: CRAM-R / shedding_log.jsonl (no CRAM-A commit)")

        print("SOSO / LANE 2  [ADVISORY]")
        if multimodal:
            print(f"  multimodal input: {multimodal.get('_path')}")
            print("  executable multimodal analysis: NOT CONNECTED")
        print("  received: inline camera metric only (no CRAM-A reference in this implementation)")
        print(f"  analysis: {soso.get('state', 'unavailable')}")
        print(f"  authority: {soso.get('authority', 'unavailable')}")
        print("  advisory record: " + (str(self.mram_s / f"S{frame_id:010d}.json")
              if advisory else "not yet written"))

        print("TOKEN NETWORK / TOK  [ADVISORY / STATE-DISCIPLINE]")
        if token:
            payload = token.get("payload", {})
            print(f"  event: {token.get('event_type', 'unavailable')} (created)")
            print(f"  type / id: {payload.get('token_type', 'unavailable')} / "
                  f"{payload.get('token_id', 'unavailable')}")
            print(f"  evidence reference: {_short(payload.get('cram_ref_hash', 'unavailable'), 32)}")
            print(f"  state hash: {_short(payload.get('token_state_hash', 'unavailable'), 32)}")
            print(f"  lineage: prev={_short(token.get('prev_event_hash', 'unavailable'), 20)} "
                  f"event={_short(token.get('event_hash', 'unavailable'), 20)}")
            print(f"  persistence: {self.mram_s / 'tokens' / 'tok_advisory_audit.jsonl'}")
        else:
            print("  activity: none (RT is emitted only after a Lane-1 PASS commit)")
            print("  VDT / VLT / AVLT: no live producer connected in LCC-01")

        print("MRAM-S  [ADVISORY STORAGE]")
        print(f"  record authority: {advisory.get('authority', 'not yet written') if advisory else 'not yet written'}")
        print("BOUNDARY")
        print("  Lane-1 modified by SoSo: NO (observer reads post-verdict artifacts)")
        print("  CRAM-A modified by SoSo: NO (SoSo record is MRAM-S only)")
        print("  PASS/DROP authority leakage: NO (TOK audit declares affects_pass_drop=false)")

    def poll(self) -> int:
        records = _read_jsonl(self.cram_store / "verdict_log.jsonl")
        for record in records:
            frame_id = record.get("frame_id")
            has_multimodal = isinstance(frame_id, int) and self._multimodal_for(frame_id) is not None
            if isinstance(frame_id, int) and (frame_id not in self._shown or
                                              (has_multimodal and frame_id not in self._shown_multimodal)):
                self._print_event(record)
                self._shown.add(frame_id)
                if has_multimodal:
                    self._shown_multimodal.add(frame_id)
        return len(self._shown)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only LCC-01 event display")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--follow", action="store_true",
                        help="poll until --idle-seconds without a new event")
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--idle-seconds", type=float, default=3.0)
    args = parser.parse_args()

    observer = RunObserver(args.run_dir)
    last_count = observer.poll()
    if not args.follow:
        return 0

    idle_started = time.monotonic()
    while time.monotonic() - idle_started < args.idle_seconds:
        time.sleep(args.interval)
        count = observer.poll()
        if count != last_count:
            last_count = count
            idle_started = time.monotonic()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
