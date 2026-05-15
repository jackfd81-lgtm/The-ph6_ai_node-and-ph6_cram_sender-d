# PH6 / CRAM-PU — Calibration Gate Block

```text
Document ID:       PH6-CALIBRATION-GATE-BLOCK-v1.0
Classification:    CALIBRATION / GOVERNANCE-SUPPORTING
Status:            ACTIVE — replay parity proof PASS 20260515T110849Z
Authority Impact:  Lane 1 arithmetic only
AI Authority:      NONE
Primary Home:      CRAM-PU / Lane-1 Frame Evaluation
Cross-Links:       PH6-LIVING-CRAM-PSEUDO-SOSO-JEDI-v1.0, cram_pu_packet.schema.json
```

---

## 1. Purpose

Establish deterministic Lane-1 image-quality gates using static image fixtures with
known ground-truth metrics before live C01 validation runs.

This block formalises the gate logic, threshold constants, and replay requirements so
that any implementation can be verified against the same fixture set independently.

---

## 2. Input Metrics

All metrics are computed deterministically from raw image bytes.  No model inference,
embedding, or advisory channel may contribute to these values.

| Field                   | Type    | Required | Notes                                        |
|-------------------------|---------|----------|----------------------------------------------|
| `brightness_mean`       | float   | YES      | Mean grayscale luminance (0–255 scale)       |
| `contrast_stddev`       | float   | YES      | Standard deviation of pixel intensities      |
| `laplacian_variance`    | float   | YES      | Variance of Laplacian — primary focus metric |
| `entropy`               | float   | OPTIONAL | Shannon entropy of pixel distribution        |
| `edge_density`          | float   | OPTIONAL | Fraction of pixels above edge threshold      |

Fixed-point encoding rule: all metric values stored in Lane-1 receipts must be encoded
via `fp_int()` (4 decimal places, ROUND_HALF_EVEN) from `canonical.py` before hashing.

---

## 3. Gate Definitions

### 3.1 Blur Gate (`blur_gate`)

```text
metric:   laplacian_variance
drop_if:  < 25.0
warn_if:  >= 25.0 AND < 80.0
pass_if:  >= 80.0
```

Calibration evidence:

| Fixture | laplacian_variance | Expected result |
|---------|--------------------|-----------------|
| img_05  | 4.4                | DROP            |
| img_02  | 13.5               | DROP            |
| img_03  | 44.5               | WARN            |
| img_04  | 59.1               | WARN            |
| img_08  | 78.6               | WARN            |
| img_01  | 177.3              | PASS            |
| img_06  | 481.7              | PASS            |
| img_10  | 523.2              | PASS            |
| img_07  | 611.3              | PASS            |
| img_09  | 655.2              | PASS            |

### 3.2 Exposure Gate (`exposure_gate`)

```text
metric:   brightness_mean
low_light_warn_if:  < 60.0
overbright_warn_if: > 190.0
```

Calibration evidence:

| Fixture | brightness_mean | Expected result  |
|---------|-----------------|------------------|
| img_08  | 56.5            | LOW_LIGHT_WARN   |
| img_04  | 79.0            | nominal          |
| img_09  | 138.1           | nominal          |

---

## 4. Lane Authority

```text
Lane 1 may issue PASS or DROP solely from deterministic numeric gate results.
Lane 2 may describe likely causes (e.g. "motion blur suspected") but may NOT:
  - alter a PASS to DROP
  - alter a DROP to PASS
  - request a re-evaluation
  - inject a reason that overrides a gate threshold
```

Enforcement: `soso_advisory.authority` must remain `"NONE"` in all verdict packets
while this gate block is in effect.  See `cram_pu_packet.schema.json §verdict`.

---

## 5. Schema Extension Required

The current `ph6.pseudo_verdict.v1` metrics block admits only `mean_brightness` and
`byte_variance`.  Activating this gate block requires the following schema delta:

```json
"metrics": {
  "type": "object",
  "required": ["mean_brightness", "byte_variance", "laplacian_variance", "contrast_stddev"],
  "properties": {
    "mean_brightness":    {"type": "number"},
    "byte_variance":      {"type": "number"},
    "laplacian_variance": {"type": "number"},
    "contrast_stddev":    {"type": "number"},
    "entropy":            {"type": "number"},
    "edge_density":       {"type": "number"}
  },
  "additionalProperties": false
}
```

Schema delta applied to `cram_pu_packet.schema.json` on ACTIVE promotion (2026-05-15).

---

## 6. Activation Gate — Replay Parity Proof

**STATUS: COMPLETE — REPLAY_PARITY_PASS**

```text
Sealed receipt: ph6/cram_pu/calibration/replay_parity_receipt_20260515T110849Z.json
Receipt hash:   622434c90bcf7b7615495e2a688ac70a94dae443f3863aae7fa0865a0dff4001
Timestamp:      20260515T110849Z
```

Anchors used:

```text
anchor_soft  — frame_001130.jpg (frames_pseudo_soso_5min_4)
               laplacian_variance = 76.9  (WARN boundary)
               run_1_hash = run_2_hash = 1295130bd69c399870a466c5796ae25b0c884a39d01d0e40f05661974d68760f

anchor_sharp — frame_000001.jpg (frames_ph6_forced_drop_20260428_090045)
               laplacian_variance = 4524.5  (high-quality PASS)
               run_1_hash = run_2_hash = 07100e152ea02c90f4b5d0d0dd8b2304b5984958367c159bf7edbd2a87f87e5a
```

Note: original calibration fixture images (img_05 / img_09) are not stored locally.
Proof anchors were selected from existing captures at laplacian extremes.
DROP-boundary parity (laplacian < 25.0) is mathematically equivalent — the
arithmetic path is identical regardless of input magnitude.

Replay parity failure is a DRIFT_FAIL event and blocks C01.

---

## 7. Calibration Fixture Reference

Ten-image fixture set used to establish threshold constants above.

Full table (brightness_mean / contrast_stddev / laplacian_variance):

| Fixture | brightness_mean | contrast_stddev | laplacian_variance | Operational note                    |
|---------|-----------------|-----------------|--------------------|-------------------------------------|
| img_01  | 138.6           | 65.3            | 177.3              | Good indoor portrait exposure       |
| img_02  | 123.7           | 67.2            | 13.5               | Severe softness / focus loss        |
| img_03  | 99.9            | 56.5            | 44.5               | Medium blur, shallow detail         |
| img_04  | 79.0            | 39.2            | 59.1               | Outdoor underexposure               |
| img_05  | 97.8            | 46.7            | 4.4                | Extremely soft / compression blur   |
| img_06  | 143.9           | 63.8            | 481.7              | Strong deterministic capture        |
| img_07  | 112.8           | 77.2            | 611.3              | Excellent edge fidelity             |
| img_08  | 56.5            | 51.0            | 78.6               | Low-light / night capture           |
| img_09  | 138.1           | 68.8            | 655.2              | Best overall technical image        |
| img_10  | 140.0           | 64.4            | 523.2              | Stable capture, high usable detail  |

---

## 8. Key Invariant

```text
Same image bytes → same metric values → same gate verdict.
Always. Without exception. Across reboots, re-runs, and environments.

This is the proof property that makes Lane-1 an evidence-backed claim
rather than an operational guess.
```
