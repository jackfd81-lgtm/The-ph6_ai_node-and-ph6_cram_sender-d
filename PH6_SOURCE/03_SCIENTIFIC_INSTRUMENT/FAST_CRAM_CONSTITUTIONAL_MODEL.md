================================================================================
PH6 FAST CRAM CONSTITUTIONAL MODEL
================================================================================
Classification : CANON — Book II / Book III
Ingest order   : 00_READ_FIRST -> Book 0 -> Book I -> THIS FILE -> Book III
Authority      : FULL
Version        : SMI-1.2
================================================================================

================================================================================
SESSION PRECHECK -- READ BEFORE TOUCHING ANY CODE
================================================================================

Before any action, confirm ALL of the following:

  [1] Lane 1 authority boundaries understood
  [2] FAST CRAM is NOT final authority
  [3] PSEUDO-A is the ONLY source of PASS/DROP
  [4] Lane 2 authority = ZERO -- no exceptions
  [5] RSYNC = Priority Zero -- never blocked under any condition
  [6] Canonical field = motion_fraction
      FORBIDDEN: motion_score | motion_decay_score

If uncertain about ANY item:
  STOP. Do not proceed. Do not assume. Do not autocorrect.

================================================================================
CORE RULE
================================================================================

FAST CRAM exists so the Tricorder does not lose speed.
FAST CRAM preserves continuity of capture -- NOT final truth.

Final truth requires TWO things:
  (1) deterministic adjudication  ->  PSEUDO-A
  (2) authoritative seal          ->  SLOW CRAM

FAST CRAM IS:
  - governed staging lane
  - bounded acceleration layer
  - replay-visible buffer
  - pre-authority preservation system

FAST CRAM IS NOT:
  - final authority
  - proof-complete storage
  - PASS/DROP authority
  - authoritative evidence truth

================================================================================
PIPELINE -- CORRECT ORDER
================================================================================

  FAST Capture
      |
      v
  FAST CRAM staging         [state: PENDING_SEAL -- PRE-AUTHORITY]
      |
      v
  PSEUDO-M measurement      [deterministic metrics only -- no authority]
      |
      v
  PSEUDO-A adjudication     [issues: PASS or DROP -- sole authority]
      |
      v
  SLOW CRAM seal            [CRAM-A (PASS) or CRAM-R (DROP) -- final authority]
      |
      v
  RSYNC export              [Priority Zero -- never blocked]

WRONG ORDER (forbidden):
  capture -> immediate full proof seal -> then measurement

================================================================================
LANE TABLE
================================================================================

  Lane    Name                  Job                                   Authority
  ------  --------------------  ------------------------------------  --------------------
  F       FAST Capture          Grab frames/sensors rapidly           NONE
  FC      FAST CRAM             Stage evidence quickly                PRE-AUTHORITY
  P       PSEUDO                Measure + PASS/DROP                   AUTHORITATIVE DECISION
  SC      SLOW CRAM             Atomic seal + authoritative store     FINAL AUTHORITY STORAGE
  2       Advisory/SoSo/TOK     Mapping / continuity / clustering     ZERO
  5       RSYNC                 Export continuity                     PRIORITY ZERO

================================================================================
OBJECT STATUS STATES
================================================================================

  CAPTURED        Sensor observed signal
  STAGED          FAST CRAM preserved object
  PENDING_SEAL    Awaiting authority-safe seal
  MEASURED        PSEUDO-M completed metrics
  ADJUDICATED     PASS/DROP issued by PSEUDO-A
  SEALED_PASS     Final CRAM-A authority object
  SEALED_DROP     Final CRAM-R reject object
  EXPORTED        RSYNC completed
  LOST_UNSEALED   Crash occurred before authority-safe seal

================================================================================
PSEUDO CONSTRAINTS
================================================================================

PSEUDO-M computes (all fixed-point, no raw floats):
  entropy_fp        Shannon entropy
  laplacian_var_fp  Laplacian variance
  motion_fraction   CANONICAL -- NOT motion_score, NOT motion_decay_score

PSEUDO-A issues:
  PASS  or  DROP  -- nothing else, ever

PSEUDO invariants (all must hold):
  - deterministic only
  - no probabilistic authority
  - thresholds fixed at design time -- replay-stable
  - no ML adjudication
  - no advisory override
  - identical input -> identical verdict, always

================================================================================
FAST CRAM -- ALLOWED vs FORBIDDEN
================================================================================

ALLOWED:
  - capture rapidly
  - stage frames
  - preserve short-window evidence
  - absorb burst ingest pressure
  - queue deterministic work
  - temporarily use RAM acceleration
  - feed SLOW CRAM
  - degrade gracefully under overload

FORBIDDEN:
  - claim final authority
  - bypass PSEUDO-A
  - finalize CRAM-A directly
  - rewrite sealed evidence
  - suppress unsealed loss
  - violate replay guarantees
  - allow Lane 2 authority influence
  - block RSYNC

================================================================================
SLOW CRAM SEAL CONTRACT
================================================================================

PASS path -> CRAM-A:
  write(tmp) -> fsync(file) -> rename() -> fsync(dir)   [atomic -- never skip]
  BLAKE2b-256 authority marker (.blake2b)
  canonical JSON serialization (sort_keys=True, ensure_ascii=False, allow_nan=False)
  authoritative metadata emission
  audit receipt generation (event_seq + authority_hash -- both required)
  replay continuity preservation

DROP path -> CRAM-R:
  same atomic write contract
  verdict = DROP sealed permanently, never mutable

Violation of atomic write contract invalidates authoritative trust.

================================================================================
AUDIT SCHEMA -- ph6.audit_event.v1
================================================================================

Required fields (additionalProperties: false -- no extras permitted):

  schema           "ph6.audit_event.v1"
  event_seq        monotonic integer, process-safe
  event_type       e.g. FRAME_VERDICT / PROMOTE / DROP
  object_id        canonical CRAM object identifier
  event_hash       BLAKE2b-256 of body (excluding event_hash itself)
  prev_event_hash  BLAKE2b-256 of previous event, or "GENESIS" for first
  authority_hash   BLAKE2b-256 of Lane-1 verdict payload
                   OR "0" * 64 (ZERO_HASH) for Lane-2/advisory events
  ts               UTC ISO-8601

Lane-2 events: authority_hash = ZERO_HASH sentinel
Lane-2 events are recorded in chain but structurally distinguished.
Missing authority_hash = schema violation = raise ValueError immediately.

================================================================================
RSYNC SOVEREIGNTY
================================================================================

RSYNC = Priority Zero. Nothing may block it. Not:
  AI / SoSo / TOK / Swarm / rendering / indexing /
  dashboards / analytics / clip generation / thermal analysis

Under pressure, ALL of the above yield to RSYNC.

RSYNC must preserve:
  - hash continuity
  - authority integrity
  - replay consistency

RSYNC may NEVER mutate authoritative evidence.

================================================================================
RECOVERY DOCTRINE
================================================================================

After crash or power loss:
  sealed evidence   ->  remains authoritative, unchanged
  staged evidence   ->  reclassified -- never promoted to authority
  audit chain       ->  must expose recovery state honestly
  replay            ->  reconstruction may occur from sealed evidence only

Governing recovery question:
  "What is provably true after failure?"

Unsealed evidence is NEVER treated as proven evidence.

================================================================================
OPERATING MODES
================================================================================

  LIVE FAST        Maximum acquisition speed
  FAST CRAM        Fast staging + deferred sealing
  STRICT CRAM      Immediate atomic authority writes (forensic mode)
  RECOVERY         Reconcile staged vs sealed truth after crash
  EXPORT PRIORITY  Advisory work yields to RSYNC
  DEGRADED         Preserve capture + export first; everything else last

================================================================================
DETERMINISTIC RULES
================================================================================

SYSTEM MUST:
  - produce repeatable verdicts
  - preserve replay equivalence
  - maintain explicit authority boundaries
  - preserve sequence monotonicity
  - expose crash state honestly
  - separate staging from proof

SYSTEM MUST NEVER:
  - silently promote staged data into authority truth
  - allow AI to issue PASS/DROP
  - mutate sealed evidence
  - allow advisory outputs into Lane P
  - permit hidden post-seal mutation
  - allow export starvation

================================================================================
MOTION FIELD DOCTRINE
================================================================================

NONCANONICAL FIELD NAMES (do not use):
  motion_score
  motion_decay_score

CANONICAL MOTION METRIC:
  motion_fraction

Motion analysis itself is REQUIRED.

PH6 explicitly permits:
  - deterministic motion measurement
  - movement persistence analysis
  - motion continuity analysis
  - bounded motion classification
  - velocity estimation
  - motion topology
  - multi-frame movement analysis
  - deterministic temporal tracking

What is forbidden:
  - ambiguous scoring terminology
  - probabilistic motion authority
  - undefined semantic scoring
  - non-replayable motion interpretation

Motion measurement is mandatory.
Ambiguous motion authority terminology is forbidden.

================================================================================
CANONICAL STATEMENT
================================================================================

  FAST Capture    acquires reality.
  FAST CRAM       preserves speed.
  PSEUDO          determines truth.
  SLOW CRAM       preserves proof.
  Lane 2          advises without authority.
  RSYNC           preserves sovereignty.

================================================================================
CONFLICT RESOLUTION RULE
================================================================================

  Newest explicit instruction
  -> Clearest technical source
  -> Safest default

  Book doctrine overrides implementation.
  Certification proves doctrine.
  Certification may NOT redefine doctrine.

================================================================================
END -- FAST CRAM CONSTITUTIONAL MODEL
Next read: Book III -- Boundary Containment Annex (what is forbidden)
================================================================================
