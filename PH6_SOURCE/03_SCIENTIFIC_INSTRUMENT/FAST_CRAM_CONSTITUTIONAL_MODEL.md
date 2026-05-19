# PH6 FAST CRAM CONSTITUTIONAL MODEL
# Classification: CANON — Book II / Book III
# Ingest order: after 00_READ_FIRST, after Book 0, after Book I
# Authority: FULL
# Version: SMI-1.1

# ── SESSION PRECHECK ──────────────────────────────────────────────────────────
#
# Before touching any code, Claude Code must confirm:
#
#   [ ] Lane 1 authority boundaries understood
#   [ ] FAST CRAM ≠ final authority
#   [ ] PSEUDO-A is the ONLY source of PASS/DROP
#   [ ] Lane 2 authority = ZERO
#   [ ] RSYNC = Priority Zero, never blocked
#   [ ] motion_fraction is canonical (NOT motion_score, NOT motion_decay_score)
#
# If uncertain about any item: STOP. Do not proceed. Do not autocorrect.

# ── CORE RULE ─────────────────────────────────────────────────────────────────

FAST CRAM exists so the Tricorder does not lose speed.
FAST CRAM preserves continuity of capture — NOT final truth.

Final truth requires:
  deterministic adjudication  (PSEUDO-A)
  + authoritative seal        (SLOW CRAM)

FAST CRAM IS:   governed staging lane
                bounded acceleration layer
                replay-visible buffer
                pre-authority preservation system

FAST CRAM IS NOT: final authority
                  proof-complete storage
                  PASS/DROP authority
                  authoritative evidence truth

# ── PIPELINE ─────────────────────────────────────────────────────────────────

FAST Capture
    → FAST CRAM staging        [PRE-AUTHORITY — PENDING_SEAL]
    → PSEUDO-M measurement     [deterministic metrics only]
    → PSEUDO-A adjudication    [PASS or DROP — sole authority]
    → SLOW CRAM seal           [CRAM-A or CRAM-R — final authority]
    → RSYNC export             [Priority Zero — never blocked]

NOT:
    capture → immediate full proof seal → then measurement

# ── LANE TABLE ───────────────────────────────────────────────────────────────

Lane F   FAST Capture       Grab frames/sensors rapidly          NONE
Lane FC  FAST CRAM          Stage evidence quickly               PRE-AUTHORITY
Lane P   PSEUDO             Measure + PASS/DROP                  AUTHORITATIVE DECISION
Lane SC  SLOW CRAM          Atomic seal + authoritative store    FINAL AUTHORITY STORAGE
Lane 2   Advisory/SoSo/TOK  Mapping / continuity / clustering   ZERO
Lane 5   RSYNC              Export continuity                    PRIORITY ZERO

# ── STATUS STATES ─────────────────────────────────────────────────────────────

CAPTURED       Sensor observed signal
STAGED         FAST CRAM preserved object
PENDING_SEAL   Awaiting authority-safe seal
MEASURED       PSEUDO-M completed metrics
ADJUDICATED    PASS/DROP issued by PSEUDO-A
SEALED_PASS    Final CRAM-A authority object
SEALED_DROP    Final CRAM-R reject object
EXPORTED       RSYNC completed
LOST_UNSEALED  Crash occurred before authority-safe seal

# ── PSEUDO CONSTRAINTS ────────────────────────────────────────────────────────

PSEUDO-M computes:
  entropy_fp        (Shannon entropy, fixed-point)
  laplacian_var_fp  (Laplacian variance, fixed-point)
  motion_fraction   (canonical field — NOT motion_score, NOT motion_decay_score)

PSEUDO-A issues:
  PASS  or  DROP  — nothing else

PSEUDO invariants:
  deterministic only
  no probabilistic authority
  thresholds fixed at design time — replay-stable
  no ML adjudication
  no advisory override
  identical input → identical verdict — always

# ── FAST CRAM: ALLOWED ────────────────────────────────────────────────────────

  capture rapidly
  stage frames
  preserve short-window evidence
  absorb burst ingest pressure
  queue deterministic work
  temporarily use RAM acceleration
  feed SLOW CRAM
  degrade gracefully under overload

# ── FAST CRAM: FORBIDDEN ──────────────────────────────────────────────────────

  claim final authority
  bypass PSEUDO-A
  finalize CRAM-A directly
  rewrite sealed evidence
  suppress unsealed loss
  violate replay guarantees
  allow Lane 2 authority influence
  block RSYNC

# ── SLOW CRAM SEAL CONTRACT ───────────────────────────────────────────────────

PASS → CRAM-A:
  full atomic write contract
  write(tmp) → fsync(file) → rename() → fsync(dir)
  BLAKE2b-256 authority marker (.blake2b)
  canonical JSON serialization
  authoritative metadata emission
  audit receipt generation (event_seq + authority_hash required)
  replay continuity preservation

DROP → CRAM-R:
  same atomic contract
  verdict = DROP sealed permanently

# ── AUDIT SCHEMA ─────────────────────────────────────────────────────────────

Required fields (ph6.audit_event.v1):
  schema
  event_seq        (monotonic, process-safe)
  event_type
  object_id
  event_hash       (BLAKE2b-256 of body excluding event_hash)
  prev_event_hash  (GENESIS for first event)
  authority_hash   (BLAKE2b-256 of Lane-1 verdict payload
                    OR ZERO_HASH sentinel for Lane-2 events)
  ts

Schema sealed with: additionalProperties: false

Lane-2 events: authority_hash = "0" * 64 (ZERO_HASH sentinel)
Lane-2 events are recorded but structurally distinguished.

# ── RSYNC SOVEREIGNTY ─────────────────────────────────────────────────────────

RSYNC = Priority Zero. Nothing may block it.

Under pressure, these yield:
  Lane 2 / SoSo / TOK / clustering / analytics
  replay analysis / token mapping / rendering / indexing

RSYNC must preserve:
  hash continuity
  authority integrity
  replay consistency

RSYNC may never mutate authoritative evidence.

# ── RECOVERY DOCTRINE ────────────────────────────────────────────────────────

After crash or power loss:
  sealed evidence     → remains authoritative
  staged evidence     → reclassified, not promoted
  replay              → reconstruction may occur
  audit chain         → must expose recovery state

Governing recovery question:
  "What is provably true after failure?"

Unsealed evidence is NEVER treated as proven evidence.

# ── OPERATING MODES ──────────────────────────────────────────────────────────

LIVE FAST       Maximum acquisition speed
FAST CRAM       Fast staging + deferred sealing
STRICT CRAM     Immediate atomic authority writes (forensic mode)
RECOVERY        Reconcile staged vs sealed truth after crash
EXPORT PRIORITY Advisory work yields to RSYNC
DEGRADED        Preserve capture + export first; advisory last

# ── DETERMINISTIC RULES ───────────────────────────────────────────────────────

SYSTEM MUST:
  produce repeatable verdicts
  preserve replay equivalence
  maintain explicit authority boundaries
  preserve sequence monotonicity
  expose crash state honestly
  separate staging from proof

SYSTEM MUST NEVER:
  silently promote staged data into authority truth
  allow AI to issue PASS/DROP
  mutate sealed evidence
  allow advisory outputs into Lane P
  permit hidden post-seal mutation
  allow export starvation

# ── SCIENTIFIC INSTRUMENT DOCTRINE ───────────────────────────────────────────

PH6 is fundamentally a deterministic scientific instrument.

Priority hierarchy:
  1. Measurement validity
  2. Deterministic reproducibility
  3. Chain-of-custody integrity
  4. Replay equivalence
  5. Advisory interpretation

The Tricorder preserves:
  measurable signal
  deterministic metrics
  replayable evidence states
  mathematically explainable adjudication

Not beliefs.

# ── FAST vs STRICT DOCTRINE ──────────────────────────────────────────────────

STRICT CRAM optimizes for:
  immediate proof certainty
  maximum atomic integrity
  minimum ambiguity
  Cost: reduced throughput, increased latency

FAST CRAM optimizes for:
  live responsiveness
  burst absorption
  field continuity
  high-rate acquisition
  Cost: temporary uncertainty window, bounded crash-loss risk

This tradeoff is lawful because PH6 explicitly distinguishes:
  observed ≠ sealed

# ── ADVISORY DOCTRINE ────────────────────────────────────────────────────────

Lane 2 exists for:
  continuity estimation
  mapping
  topology assistance
  clustering
  operator guidance
  post-analysis

Lane 2 does NOT exist for:
  authority
  adjudication
  evidence sealing
  replay truth mutation
  deterministic gate override

All Lane 2 outputs are advisory artifacts only.
Authority remains exclusively inside Lane P + SLOW CRAM.

# ── RAM CLARIFICATION ────────────────────────────────────────────────────────

RAM may be used for:
  bounded buffering
  ingest acceleration
  temporary queues
  replay assistance
  short-lived staging

RAM is NOT authority storage.

Loss of RAM-backed staged data before seal is lawful only if:
  detectable
  auditable
  never falsely represented as sealed evidence

# ── FORBIDDEN FIELDS ─────────────────────────────────────────────────────────

FORBIDDEN:  motion_score
FORBIDDEN:  motion_decay_score
CANONICAL:  motion_fraction

# ── CANONICAL STATEMENT ───────────────────────────────────────────────────────

FAST Capture    acquires reality.
FAST CRAM       preserves speed.
PSEUDO          determines truth.
SLOW CRAM       preserves proof.
Lane 2          advises without authority.
RSYNC           preserves sovereignty.

# ── CONFLICT RULE ─────────────────────────────────────────────────────────────

Newest explicit instruction
→ Clearest technical source
→ Safest default

Book doctrine overrides implementation.
Certification proves doctrine.
Certification may NOT redefine doctrine.

# END FAST CRAM CONSTITUTIONAL MODEL
# Next read: Book III — Boundary Containment Annex (what is forbidden)
