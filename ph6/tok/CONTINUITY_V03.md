# CRAM-based Reference Token continuity — first v0.3 migration increment

PROPOSED implementation; Authority ZERO. Operator architectural direction is
recorded in `PH6_LOCAL_BACKUPS/PH6_V03_ARCHITECTURAL_BASELINE_20260921/`.
This document registers the advisory interfaces in this increment; it does not
ratify a sensor profile, change canon, or establish production qualification.

## Contract and scope

Durable CRAM preservation is upstream of advisory processing. The two primary
capture runners now instantiate a notification client, not a TokenStore. A PASS
commit is followed by a bounded nonblocking Unix datagram attempt. The client
does no token/audit/materialization I/O and performs no retry or acknowledgment
wait. The separate per-frame SoSo snapshot write also leaves these two capture
loops. Existing deterministic measurement and adjudication functions are intact.

The compatibility name `_TokSidecar` remains for older campaign callers, but its
meaning changes to notification only. `rt_count()` returns `None`: the producer
cannot know how many tokens a separate worker completed. Capture manifests must
not equate queue admission with completion. Older campaign tools may still do
other synchronous advisory work; this increment does not qualify every caller.

`CRAMReconciler` reads an explicit allowlist of CRAM stores. Its output must be in
a disjoint, new MRAM-S namespace. Incoming hints cannot add stores or supply
trusted measurements. Scans work with no notifications at all, including after
the worker was absent during the entire acquisition run. Configure each actual
CRAM store before relying on eventual recovery; an unknown directory cannot be
discovered magically from a lost notification. Configuration belongs to worker
startup, never to a persistent registration write in the capture loop.

This first increment covers RT references to committed PASS records in the
existing `ph6.cram_commit.v1` layout. It does not implement CRAM-R representations,
VDT/VLT production, general COIN processing, or idempotent SSMT packet replay.
Existing SSMT notifications and processing remain compatible and separate.

## Registered interfaces

| Identifier | Fields and semantics |
| --- | --- |
| `ph6.tok.handoff.v1` | Exact keys: schema, cram_ref (string, at most 1,024 characters), payload_hash (lowercase 64-character BLAKE2b-256 hex), frame_id (positive integer below 10^10). At most 4,096 encoded bytes. No authority, verdict, or mutable sensor policy can be supplied. |
| `ph6.tok.handoff_accounting.v1` | Authority ZERO, advisory_only true; attempts, outcomes ADMITTED/SHED/FAILED/BYPASSED, token_completion UNKNOWN, scope PROCESS_LIFETIME_COUNTERS. |
| `ph6.tok.cram_coverage.v1` | Authority ZERO, advisory_only true; coverage_scope COMMITTED_PASS_REFERENCE_TOKENS, per-store discovered/reconciled counts, contiguous_watermark and unresolved record list, token_count and notifications_admitted. Health snapshots may include processed_this_scan. |
| `ph6.tok.cram_advisory.v1` | Authority ZERO, advisory_only true; cram_ref_hash, frame_id, optional reconstructed soso context, soso_status RECOVERED or UNAVAILABLE. No new measurement or verdict. |
| `ph6.cram_pu.live_manifest.v2` | Retains capture-manifest fields, changes tok_rt_count to null/unknown, adds tok_handoff accounting. |
| `ph6.lcc01_final_manifest.v2` | Same explicit unknown token count and separate handoff accounting for the camera runner. Camera policy and other manifest fields are unchanged. |

ADMITTED means the datagram was accepted by the local socket operation. It does
not prove worker receipt, a durable queue, or token completion. SHED means kernel
queue/buffer saturation; FAILED includes unavailable IPC or invalid/oversized
inputs; BYPASSED means notifications are disabled. Producer counters are bounded
memory state. A producer crash can lose them. Existing capture end reports and
optional frame-metrics logs expose those counters/outcomes; they are not an
authoritative delivery journal. Reconciliation finds the underlying committed
records regardless of those counters.

`--tok-disabled` controls notification attempts. A separately configured worker
can still recover that store. For a true no-advisory control, exclude the store
from worker configuration or stop the test worker; do not assume notification
disablement deletes or vetoes worker-visible CRAM evidence.

## Discovery, identity and coverage

Stores are ordered by canonical resolved path; records by their fixed-width
`cram_##########.json` names. Frame-number gaps are allowed because DROP records
are not PASS commits. For each candidate the worker checks schema and Lane-1
envelope, record hash, predecessor link, commit marker and preserved payload
hash. A missing marker is unresolved and may be retried after capture completes
its atomic commit. Corrupt, missing or rewritten previously observed records
cannot be silently skipped. Symlinked records/payloads and escaped roots are
refused. The worker imports no Lane-1 authorization or commit API.

Reference identity is the committed CRAM record hash, not merely the payload
hash. Thus two observations with identical payload bytes retain distinct RTs
when their commits differ; identical preserved replicas share a reference.
Token IDs and timestamps are deterministic functions of the preserved commit.
Payload hash and frame ID are retained as token metadata. Legacy token directories
are preserved: this implementation uses `continuity-v03/tokens` rather than
silently changing the identity scheme of pre-existing materializations.

Coverage lives in `coverage.sqlite3`, with synchronous FULL transactions and a
startup integrity check. Per-record states include DISCOVERED, PROCESSED,
RECONCILED, FAILED and UNRESOLVED. Notification admission is recorded separately.
The contiguous watermark is derived from the uninterrupted RECONCILED prefix;
higher entries cannot conceal lower unfinished records. It is not a maximum
frame ID or a substitute for the per-record gap ledger. This database is
reconstructable advisory state; checks against CRAM and token audit evidence are
performed independently of its claims.

Coverage means the RT is durably represented and checked. Optional SoSo context
is copied from the matching preserved verdict record, with Authority ZERO. If
that context is unavailable, its snapshot explicitly says UNAVAILABLE; RT
coverage does not claim a complete SoSo or SSMT lifecycle.

## Integrity and recovery

One owner holds a nonblocking lifetime flock on the new advisory namespace. A
second owner refuses startup. TOK retains the existing full-chain/checkpoint
verification on startup and append. The new code does not implement RP-12's
bounded head/predecessor append optimization or incremental materialization.
That cost is now worker work rather than capture work, but sustained throughput
still needs the separate RP-12 repair.

Startup checks the materialized RT envelope and all materialized state hashes
against the fully checked token audit. A crash after a complete token audit
append/checkpoint but before materialization is recoverable from the deterministic
CRAM-derived RT: no second RT_GENESIS is appended. A crash between the audit append
and its checkpoint remains fail-closed under the existing checkpoint contract.
No suspect checkpoint is deleted or auto-anchored. A persistence failure poisons
the current reconciler instance; restart and full verification are required.

Existing audit checkpoints share the writer's security principal. This increment
does not add an external trusted checkpoint, defend against coordinated rewriting
of all advisory artifacts, or provide automatic repair of corrupt CRAM. It never
changes CRAM bytes to resolve an advisory error.

## Operation and rollout

An isolated one-batch saved-evidence invocation is:

```bash
python3 -m ph6.tok.reconciliation \
  --root /path/to/new/mram_s/continuity-v03 \
  --cram-store /path/to/preserved/cram_store --batch 64
```

For the existing caged worker, add one or more `--cram-store /absolute/store`
arguments to its reviewed ExecStart configuration. It scans independently every
0.5 seconds after each batch, with a default budget of eight new records per
store. Its existing CPU, memory, swap, task and I/O restrictions still apply.
The service root already permits its `continuity-v03` subdirectory. Hints for
unconfigured stores are refused and logged. A missing source remains explicitly
unresolved and is retried when the configured store appears.

This source change alone does not reconfigure or restart the installed worker.
Deployment requires a concrete store allowlist. Live PASS-producing camera
qualification remains pending, along with the versioned AC-3 profile decision,
RP-12 repair and the rest of the v0.3 acceptance matrix.

Provenance: proposed_by=codex-lane2; proposed_at_utc=2026-09-22;
api_call_log_ref=PH6_V03_HANDOFF_20260922; ratified_by=null.
