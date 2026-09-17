#!/usr/bin/env python3
"""
verify_vectors.py — updated 2026-09-03 for the unified scaffold layout.

CHANGE LOG (disclosed, not silent):
  - Paths remapped to 03_VERIFICATION_AND_TESTS/ and 06_AUDIT_AND_LOGS/
    for the new folder layout. Evaluation logic is UNCHANGED.
  - NOT FIXED, flagged instead: this still runs on raw Python float
    (math.sqrt, division). If fp()/ph6.canonjson.v1 are locked canon,
    this needs a real fixed-precision rewrite — I don't have the fp()
    spec (rounding mode, scale) in any uploaded source, so I'm not
    guessing one. Needs a source doc or your explicit definition before
    this gets rewritten.
"""
import json, math, platform, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def mean(vals):
    return sum(vals) / len(vals)

def std_pop(vals):
    mu = mean(vals)
    return math.sqrt(sum((x - mu) ** 2 for x in vals) / len(vals))

def zscore(current, hist):
    sigma = std_pop(hist)
    mu = mean(hist)
    if sigma == 0:
        if current == mu:
            return 0.0
        return float("inf")
    return (current - mu) / sigma

def evaluate_vector(frames, cfg):
    th = cfg["THRESHOLDS"]
    entropy_count = 0
    motion_count = 0
    res_hist = []
    byte_hist = []
    output = []

    for frame in frames:
        verdict = "PASS"

        if frame.get("frame") == 0:
            output.append("DROP")
            res_hist.append(frame["resolution"][0] * frame["resolution"][1])
            byte_hist.append(frame["bytes"])
            continue

        if frame["lap_var"] < th["LAP_VAR_MIN"]:
            verdict = "DROP"

        if frame["entropy"] < th["ENTROPY_DROP_THRESH"]:
            entropy_count += 1
        else:
            entropy_count = 0
        if entropy_count >= th["ENTROPY_PERSISTENCE"]:
            verdict = "DROP"

        if frame["motion_fraction"] < th["MOTION_STASIS_MAX"]:
            motion_count += 1
        else:
            motion_count = 0
        if motion_count >= th["MOTION_WINDOW"]:
            verdict = "DROP"

        area = frame["resolution"][0] * frame["resolution"][1]
        if len(res_hist) >= th["ZSCORE_MIN_WINDOW"]:
            res_window = res_hist[-th["ZSCORE_WINDOW"]:]
            byte_window = byte_hist[-th["ZSCORE_WINDOW"]:]
            if abs(zscore(area, res_window)) > th["ZSCORE_RESOLUTION_SIGMA"]:
                verdict = "DROP"
            if abs(zscore(frame["bytes"], byte_window)) > th["ZSCORE_BYTES_SIGMA"]:
                verdict = "DROP"

        output.append(verdict)
        res_hist.append(area)
        byte_hist.append(frame["bytes"])

    return output

def main() -> int:
    cfg = json.loads((ROOT / "03_VERIFICATION_AND_TESTS" / "constants_v1.0.json").read_text(encoding="utf-8"))
    suite = json.loads((ROOT / "03_VERIFICATION_AND_TESTS" / "golden_vectors" / "golden_vectors_v1.0.json").read_text(encoding="utf-8"))
    log = {
        "tool_version": "verify_vectors.py v1.0",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "results": []
    }
    failures = 0
    for vector in suite["vectors"]:
        actual = evaluate_vector(vector["frames"], cfg)
        expected = vector["Y_gold"]
        status = "PASS" if actual == expected else "FAIL"
        log["results"].append({"id": vector["id"], "status": status, "expected": expected, "actual": actual})
        print(f"{vector['id']}: {status}")
        if status == "FAIL":
            print(f"  expected={expected}")
            print(f"  actual  ={actual}")
            failures += 1
    (ROOT / "06_AUDIT_AND_LOGS" / "replay_validation_log.json").write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        print("REPLAY_VALIDATION_FAIL")
        return 1
    print("REPLAY_VALIDATION_PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
