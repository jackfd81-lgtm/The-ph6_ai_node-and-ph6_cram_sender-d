# Pre-C01 CRAM Spine Proof — 20260515T111525Z

```text
Label:          PRE-C01-CRAM-SPINE-PROOF
Run stamp:      20260515T111525Z
Run ID:         157817e5-ade1-452d-8e20-35c734f1f8e8
Receipt hash:   0384f3f2566d5312a746d414b2ed2f35142163960353435b0a60429ec47fb27e
Frames:         300
PASS:           206
DROP:           94
Verdict:        PASS
```

---

## What This Proves

The CRAM deterministic spine operates coherently across 300 frames:

| Invariant           | Result |
|---------------------|--------|
| Torn files          | PASS — 0 torn (atomic write contract holds) |
| PASS loss           | PASS — 0 silent losses (CRAM-A integrity) |
| DROP shedding       | PASS — 0 unlogged drops |
| Advisory isolation  | PASS — SoSo stayed in MRAM-S, 0 violations |
| CRAM integrity      | PASS — 0 hash failures, 0 chain breaks |
| RSYNC health        | PASS — not blocked |
| Continuity          | PASS — 300 matched, 0 orphan, 0 hash mismatch |

Schema validation: PASS  
Authority leakage: NONE detected

---

## What This Does NOT Prove (C01 Gaps)

These gaps must be resolved before this run can be counted as C01 closure:

| Gap | Detail |
|-----|--------|
| TOK not wired | TOK-LEAK-001 (result_set_hash with TOK=ON vs OFF) not run |
| PSEUDO metrics | Current: `mean_brightness`, `byte_variance`; C01 spec requires `entropy`, `laplacian_var`, `motion_fraction` |
| Input source | Current: synthetic packets; C01 spec requires real camera frames |
| Entry point | `ph6_console.py --frames 300 --full-stack` referenced in C01 doc does not exist |

---

## Artifact Hashes (BLAKE2b-256)

```text
manifest:       1892cbccf39448d2…
departure_log:  66a03b3c6df6ebf5…
arrival_log:    76f7b04d2680044b…
verdict_log:    188b13726c0a6fe9…
shedding_log:   ad5ec42a0d02f295…
rsync_queue:    61ad6a23ba7c8cbd…
```

Full hashes in: `ph6/cram_pu/runtime/run_20260515T111525Z/pre_c01_spine_proof_receipt.json`

---

## C01 Closure Remaining Work

1. Wire TOK into `cram_pu_live.py` — expose `--tok-enabled / --tok-disabled` toggle
2. Add `entropy`, `laplacian_var`, `motion_fraction` to `verdict_logger.py` PSEUDO metrics
3. Wire real camera input (Microdia USB or ESP32-CAM) into the pipeline entry point
4. Run TOK-LEAK-001: verify result_set_hash is identical with TOK=ON and TOK=OFF
5. Run full 300-frame run against real camera input
6. Produce `C01_CLOSURE_RECEIPT.md` with human sign-off
