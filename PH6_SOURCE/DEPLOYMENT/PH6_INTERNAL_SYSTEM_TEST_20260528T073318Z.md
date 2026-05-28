# PH6 / CRAM Internal System Test Report

**Generated UTC:** 2026-05-28T07:33:18Z
**Node:** jackjack-pi5-internal
**Test Stamp:** 20260528T073318Z
**Temp Root:** /tmp/ph6_internal_test_20260528T073318Z_l96m9i34
**Test Type:** Internal — NO USB / NO CAMERA / NO VIDEO / NO CAN / NO HAT
**Elapsed:** 0.00s

---

## Overall: PASS

| Metric | Value |
|--------|-------|
| Total checks | 20 |
| PASS | 20 |
| FAIL | 0 |
| WARN | 0 |

---

## Check Results

| Check | Status | Detail |
|-------|--------|--------|
| GATE_THRESHOLDS | PASS | entropy>=6.0 laplacian>=100.0 motion [0.01,0.75] |
| FORBIDDEN_FIELD_GUARD | PASS | ValueError raised on motion_score |
| CANONICAL_JSON_DETERMINISM | PASS | len=69, keys sorted |
| BLAKE2B256_KNOWN_VECTOR | PASS | hash=0e5751c026e543b2... |
| ATOMIC_WRITE_CONTRACT | PASS | write + overwrite both byte-exact |
| GATE_PASS_CASE | PASS | verdict=PASS |
| GATE_DROP_LOW_ENTROPY | PASS | verdict=DROP |
| GATE_DROP_LOW_LAPLACIAN | PASS | verdict=DROP |
| GATE_DROP_NO_MOTION | PASS | verdict=DROP |
| GATE_DROP_EXCESS_MOTION | PASS | verdict=DROP |
| CRAM_PASS_VERDICT | PASS | verdict=PASS |
| CRAM_PASS_FILES | PASS | all 4 CRAM-A files present (incl .blake2b last) |
| CRAM_PASS_AUTHORITY_HASH | PASS | blake2b256=014652358db408cf... |
| CRAM_DROP_VERDICT | PASS | verdict=DROP |
| CRAM_DROP_FILES | PASS | CRAM-R files present, no .blake2b marker |
| AUDIT_CHAIN_EVENTS | PASS | event_count=2 |
| AUDIT_CHAIN_HASH_VERIFY | PASS | OK |
| AUDIT_CHAIN_GENESIS | PASS | first event prev_event_hash == GENESIS |
| REPLAY_PARITY | PASS | OK |
| EXPORT_COPY | PASS | OK |

---

## Doctrine Confirmation

- Lane-2 authority: ZERO
- Hash algorithm: BLAKE2b-256 (digest_size=32)
- Motion field: `motion_fraction` only
- Forbidden fields: motion_decay_score, motion_score
- Verdict vocabulary: PASS / DROP only
- `.blake2b` marker: PASS path only, written LAST
- Atomic write: 4-step contract enforced
- USB / camera / video / CAN / HAT: NOT TOUCHED

