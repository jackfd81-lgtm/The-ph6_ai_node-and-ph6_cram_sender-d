# PH6 CRAM Lane Doctrine

**Schema:** ph6.governance.storage.cram_lane.v1  
**Status:** PROPOSED  
**Proposed by:** claude-code-lane2 | **Ratified by:** null

---

## 1. CRAM-0 — Raw Intake

CRAM-0 is the first preservation point. It captures raw sensor output before any measurement or interpretation.

**Rules:**

```
Write first — before interpretation
Preserve raw sensor output exactly
Do not alter raw intake after write
Do not compress destructively unless original is preserved
Do not allow AI access to mutate CRAM-0
Do not discard because environmental conditions changed
```

**CRAM-0 answers:** What did the sensor provide?

**Marker:** No `.blake2b` marker on CRAM-0. Raw intake is not yet adjudicated.

---

## 2. CRAM-A — Accepted Evidence

CRAM-A stores PASS frames and evidence packets. It is the primary authority evidence store.

**Rules:**

```
Immutable after write
Hash-verified (BLAKE2b-256 sole canonical hash)
Replay-certified before promotion to MRAM-S
Linked to PSEUDO-M and PSEUDO-A output records
Eligible for scientific review
Eligible for legal review
```

**CRAM-A answers:** What evidence passed deterministic adjudication?

**Marker:** `.blake2b` marker written LAST — after all other files are durable. This is the final authority seal.

---

## 3. CRAM-R — Rejected / Negative Evidence

CRAM-R stores DROP frames, failed measurements, rejected packets, and negative observations.

**Rules:**

```
Immutable after write
Not deleted merely because it failed
Used for failure analysis
Used as negative corpus for AI learning
Does not weaken CRAM-A
Does not become PASS evidence without new certified adjudication cycle
```

**CRITICAL INVARIANT: NO `.blake2b` marker on CRAM-R — EVER.**

If a `.blake2b` marker is found on a CRAM-R path: `RuntimeError` + `INVARIANT VIOLATION`. This is not a warning. This is a hard stop.

**CRAM-R answers:** What failed, dropped, or did not meet deterministic criteria?

---

## 4. MRAM-S — Advisory Memory

MRAM-S stores advisory memory. It is not an evidence store. It is a continuity and learning layer.

**Rules:**

```
Authority: ZERO
May store: SoSo continuity maps
May store: AI observations and summaries
May store: Token topology
May store: Hypotheses and posits
May store: Derived artifacts with source links
May not: override CRAM evidence
May not: override PSEUDO verdicts
May not: rewrite original evidence
May not: promote its own content to Lane 1 without operator ratification
```

**MRAM-S answers:** What did the advisory layer learn, infer, map, or question?

**Marker:** `.blake2b` marker may be written after operator ratification of MRAM-S content. Not required for advisory-only objects.

---

## 5. Lane Authority Summary

| Lane | Storage | Authority | Marker | Mutable |
|------|---------|----------|--------|---------|
| CRAM-0 | Raw intake | None yet | No | No (after write) |
| CRAM-A | PASS evidence | Lane 1 | Yes — last | No |
| CRAM-R | DROP evidence | Lane 1 negative | **NO — ever** | No |
| MRAM-S | Advisory memory | **ZERO** | Optional post-ratification | Append-only |

---

## 6. Atomic Write Contract

All CRAM writes use the 4-step atomic write:

```
1. write-tmp   (write to .tmp file)
2. fsync(fd)   (flush to storage)
3. os.replace  (atomic rename)
4. fsync(dir)  (flush directory entry)
```

The `.blake2b` marker on CRAM-A is always written after this contract completes for all other files.

---

*Lane-2 advisory document. Operator ratification required.*
