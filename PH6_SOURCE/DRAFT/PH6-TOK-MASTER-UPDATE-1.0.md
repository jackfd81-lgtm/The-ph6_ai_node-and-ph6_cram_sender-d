# PH6 / CRAM — TOK-1.0 MASTER INTEGRATION UPDATE

## Deterministic Advisory Token Topology System

### Consolidated Canonical Integration Document

```text
Document ID: PH6-TOK-MASTER-UPDATE-1.0
Classification: LANE-2 / MRAM-S / AUTHORITY ZERO
Status: DRAFT / ACTIVE DEVELOPMENT REFERENCE
Primary Home: Book V — SoSo, JEDI, Tokens, Living Observation
Cross-Links: Book 0 (interpretive control), Book III (containment), Book IV (replay exclusion)

Consolidates:
  TOK-LIFECYCLE-PRUNE-1.0
  PH6-TOK-INTEGRATION-PATCH-1.1
  PH6-TOK-COMMIT-CORRECTION-1.0
  PH6-TOK-ENHANCED-CORRECTION-1.0
  BLAKE2b doctrine additions
  Previous PH6/CRAM authority doctrine
  SoSo/JEDI/TOK advisory isolation rules
```

---

## 0. Status Seal

```text
STATUS: CONDITIONAL ACCEPTANCE
LAYER: Lane-2 Advisory
AUTHORITY: ZERO
WRITE DOMAIN: MRAM-S ONLY
PRIMARY HASH: BLAKE2b-256
REPLAY DEPENDENCY: FALSE
RSYNC IMPACT: NONE
CRAM IMPACT: NONE
PSEUDO IMPACT: NONE
```

---

## 1. TOK Mission Definition

```text
TOK-1.0 manages advisory continuity topology.

TOK does not manage truth.

TOK does not manage evidence authority.

TOK exists to:
- describe continuity
- preserve advisory topology
- track temporal persistence
- model continuity pressure
- expose advisory drift
- support SoSo/JEDI continuity analysis
- remain fully reconstructable
```

---

## 2. Core PH6 Laws

TOK inherits all PH6 kernel invariants:

```text
1. Determinism
2. Crash consistency
3. Export sovereignty
4. Replayability
5. Auditability
6. Authority separation
7. Schema law
8. Never blocks RSYNC
```

---

## 3. TOK Authority Doctrine

```text
TOK is Lane-2 only.
TOK has Authority ZERO.
TOK is advisory_only=true.
TOK replay_dependency=false.
```

TOK may never:

```text
- issue PASS
- issue DROP
- influence PASS/DROP
- alter PSEUDO
- alter thresholds
- mutate EvidencePacket
- write authority audit
- modify CRAM
- block RSYNC
- participate in replay authority
- become authoritative truth
```

---

## 4. TOK Role Inside PH6

```text
Lane 0:     Physical reality
Lane 0.5:   Smart Spigot / prefilter
Lane 1:     CRAM / PSEUDO / PASS/DROP / Authority Audit
Lane 2:     TOK / SoSo / JEDI / Swarm / MRAM-S
Lane 5:     RSYNC export
```

Critical law:

```text
Lane 2 may observe Lane 1.

Lane 1 may never depend on Lane 2.
```

---

## 5. TOK Token Types

### RT — Reference Token

Persistent anchor to committed CRAM evidence.

```python
@dataclass(frozen=True)
class RT(TokenBase):
    object_class: str
    bbox: List[float]
    confidence: float
```

Purpose:
- CRAM continuity anchor
- advisory reference point
- immutable advisory linkage

---

### VDT — Virtual Drift Token

Short-lived advisory hypothesis.

```python
@dataclass(frozen=True)
class VDT(TokenBase):
    object_class: str
    bbox: List[float]
    confidence: float
    support_count: int
    last_updated_ms: int
```

Purpose:
- candidate continuity
- weak persistence hypothesis
- promotable advisory topology

---

### VLT — Virtual Longevity Token

Reinforced continuity structure.

```python
@dataclass(frozen=True)
class VLT(TokenBase):
    object_class: str
    bbox: List[float]
    first_seen_ms: int
    last_seen_ms: int
    support_count: int
    mean_confidence: float
    centroid: List[float]
    protected: bool
```

Purpose:
- long continuity modeling
- stable advisory topology
- persistence mapping
- SoSo continuity substrate

---

## 6. BLAKE2b-256 Doctrine

### Canonical PH6 Hash

```text
BLAKE2b-256
```

Python implementation:

```python
import hashlib

def blake2b256_hex(data: bytes) -> str:
    h = hashlib.blake2b(data, digest_size=32)
    return h.hexdigest()
```

### Why BLAKE2b?

| Property                  | BLAKE2b-256 | PH6 Value               |
| ------------------------- | ----------- | ----------------------- |
| Speed                     | Excellent   | High ingest performance |
| Determinism               | Perfect     | Required                |
| Length-extension immunity | Yes         | Required                |
| Replay stability          | Excellent   | Required                |
| Parallelization           | Excellent   | High-volume ingest      |
| Configurable output       | Yes         | Fixed 256-bit canon     |
| Modern security margin    | Strong      | Long-term integrity     |

### Canonical Rule

```text
All TOK state hashes,
audit hashes,
archive hashes,
rebuild hashes,
and topology hashes
must use BLAKE2b-256.

SHA-256 may exist only for compatibility.
```

---

## 7. Canonical JSON Doctrine

All TOK serialization must use canonical JSON:

```python
json.dumps(
    obj,
    sort_keys=True,
    ensure_ascii=False,
    allow_nan=False,
    separators=(",", ":"),
)
```

Required properties:
- sorted keys
- stable ordering
- no NaN
- no Infinity
- UTF-8
- deterministic serialization

---

## 8. Atomic Write Doctrine

Required sequence:

```text
write(tmp)
→ fsync(file)
→ os.replace()
→ fsync(parent_dir)
```

Forbidden:

```python
shutil.move(...)
```

Reason:

```text
TOK follows PH6 crash discipline even though it is advisory-only.
```

---

## 9. Canonical Token Base

```python
@dataclass(frozen=True)
class TokenBase:
    token_id: str
    cram_ref_hash: str      # references CRAM evidence, not authority
    timestamp_ms: int
    token_type: TokenType

    authority: str = "ZERO"
    advisory_only: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)
```

Critical correction:

```text
authority_hash → cram_ref_hash

TOK does not possess authority.
The hash references CRAM evidence only.
```

---

## 10. Token Lifecycle

```text
RT Genesis:
  CRAM commit → RT emitted → advisory audit event

VDT Genesis:
  multiple continuity hints → VDT created → advisory hypothesis

VDT Promotion:
  multiple coherent VDTs → VLT promotion → continuity reinforcement

VLT Protection:
  operator/system advisory request → protected=true → still Authority ZERO

VDT Pruning:  aggressive — weak hypotheses expire quickly

VLT Pruning:  conservative — persistent continuity expires slowly
```

---

## 11. Promotion Logic

Promotion requires:

```text
- matching cram_ref_hash
- consistent object_class
- sufficient support count
- bounded time window
- IoU consistency
- contradiction-free state
- minimum confidence
```

### Canonical VLT ID Generation

Correct:

```python
vlt_seed = {
    "cram_ref_hash": cram_ref_hash,
    "source_vdt_ids": sorted(source_ids),
    "first_seen_ms": min_ts,
    "last_seen_ms": max_ts,
    "object_class": object_class,
}

vlt_id = "vlt_" + blake2b256_hex(vlt_seed)[:24]
```

Forbidden:

```python
f"vlt_{base_hash[:16]}_{min_ts}"
```

---

## 12. Spatial Consistency

Canonical bbox format: `[x, y, w, h]`

Required IoU helper: deterministic, bounded, fixed-format.

---

## 13. Contradiction Detection

Contradictions include:

```text
- object class mismatch
- impossible bbox geometry
- extreme size variance
- excessive confidence variance
```

Purpose: prevent false continuity promotion.

---

## 14. Advisory Audit Chain

Append-only JSONL. Schema:

```json
{
  "schema": "ph6.tok.advisory_event.v1",
  "authority": "ZERO",
  "advisory_only": true,
  "event_type": "VDT_PRUNED",
  "timestamp_ms": 0,
  "prev_event_hash": "GENESIS",
  "payload": {},
  "event_hash": "<blake2b256>"
}
```

---

## 15. Reconstruction Doctrine

TOK must be rebuildable.

Rebuild sources:

```text
CRAM references
+ RT events
+ VDT events
+ VLT events
+ prune events
+ archive records
+ advisory audit chain
```

Deterministic replay order:

```text
1. event_seq
2. timestamp_ms
3. event_hash
```

Produces: `tok_rebuild_receipt.json`

Important:

```text
TOK rebuild PASS ≠ PH6 evidence PASS
```

---

## 16. Scheduler Doctrine

Background autonomous daemon schedulers are discouraged.

Preferred:

```python
run_prune_cycle(config, current_time_ms)
```

```text
PH6 runtime orchestrates TOK.
TOK does not self-govern.
```

---

## 17. SoSo Integration

SoSo may read:
- RT topology
- VDT hypotheses
- VLT continuity
- prune pressure
- topology drift

SoSo may not:
- alter Lane 1
- alter PASS/DROP
- alter replay
- alter CRAM

---

## 18. JEDI / Swarm Integration

JEDI may analyze:
- persistence pressure
- continuity collapse
- token churn
- false consensus
- continuity reinforcement

JEDI may not:
- govern TOK
- issue verdicts
- influence PSEUDO

---

## 19. File Layout

```text
/var/ph6/mram-s/tokens/
  live_tokens.json
  tok_advisory_audit.jsonl
  archive/
  reports/
  receipts/
```

Forbidden paths:

```text
/var/ph6/cram-0/
/var/ph6/cram-a/
/var/ph6/cram-r/
/var/ph6/export/
/var/ph6/audit/
```

---

## 20. Required Module Files

```text
ph6/tok/
  __init__.py
  lifecycle.py
  geometry.py
  reconstruct.py
  scheduler.py
  rebuild.py
  validators.py
  audit_writer.py
  token_store.py
  tests/
```

---

## 21. Required Validation Tests

### Boundary Tests

```text
- forbidden authority terms
- forbidden CRAM paths
- Authority ZERO checks
- advisory_only=true checks
```

### Failure Injection

```text
TOK-FI-01 → TOK attempts CRAM write
TOK-FI-02 → TOK attempts PASS mutation
TOK-FI-03 → audit chain corruption
TOK-FI-04 → missing live token store
TOK-FI-05 → rebuild from audit
TOK-FI-06 → prune replay consistency
TOK-FI-07 → RSYNC under TOK pressure
TOK-FI-08 → forbidden scheduler behavior
```

---

## 22. Crash Discipline

TOK is advisory. But TOK still obeys:

```text
- crash consistency
- deterministic replay
- append-only audit
- canonical serialization
- bounded behavior
```

---

## 23. Explicit Rejections

```text
- uncontrolled daemon pruning
- silent exception swallowing
- mutable authority semantics
- noncanonical JSON
- nondeterministic timestamps
- SHA-only hashing
- direct CRAM mutation
- replay dependence
```

---

## 24. Final TOK Philosophy

```text
RT remembers anchors.

VDT explores continuity.

VLT remembers persistence.

SoSo interprets advisory structure.

JEDI studies continuity pressure.

CRAM remains sovereign.

PSEUDO remains authority.

TOK remains ZERO.
```

---

## 25. Final Canonical Seal

```text
TOK may remember continuity.

TOK may reconstruct advisory topology.

TOK may prune live advisory state.

TOK may never decide truth.

CRAM remains sovereign.

PSEUDO remains authoritative.

RSYNC remains Priority Zero.

Lane 1 never depends on Lane 2.
```
