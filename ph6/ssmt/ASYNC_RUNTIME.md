# Asynchronous advisory runtime (PROPOSED)

## September 22 source migration update

The first v0.3 handoff/reconciliation source increment supersedes the synchronous
TOK descriptions below for the two primary capture runners. `_TokSidecar` is now
a nonblocking notification client; token completion is reported as unknown by
capture. The separate SoSo snapshot write has moved to worker reconstruction.
Optional `--cram-store` arguments enable read-only discovery, durable coverage
and idempotent RT recovery in a new `continuity-v03` namespace. See
[`../tok/CONTINUITY_V03.md`](../tok/CONTINUITY_V03.md) for the exact scope, registered
interfaces and rollout requirements. This source increment does not itself
reconfigure the installed service, optimize per-append full verification, or
establish live camera qualification. The notes below preserve the September 19
implementation/activation history rather than describing that new source path.

Authority ZERO. VDT means Virtual Drift Token. No canon or verdict threshold changes.

The camera capture path sends a nonblocking Unix datagram only after a CRAM commit.
A separate SSMT process runs all nine swarms and writes only advisory snapshots and
its audit/checkpoint files. Queue saturation, missing service, or oversized input
returns false to the producer. There is no response path. Camera capture is not
started by installing the service. The pre-existing TOK callback remains
synchronous; this change isolates SSMT computation, not every advisory operation.

The user systemd unit configures CPUQuota=30% (0.3 of one CPU), MemoryMax=512000000,
MemorySwapMax=0, Nice=19, IOSchedulingClass=idle and a restrictive filesystem
namespace. It requires enforced cgroup limits before binding its socket. A
single worker and kernel queue bound pending notifications; there are no retries
or persistent delivery guarantees for shed advisory work.

## Current activation state

Enabled and running as the user service ph6-advisory.service after reboot.
Kernel limits verified: cpu.max=30000 100000, memory.max=512000000,
memory.swap.max=0; process IO priority idle. One saved synthetic reference
produced nine verified swarm events. No fresh camera capture was started.
See /home/jack/PH6_LOCAL_BACKUPS/advisory-hardening/post-reboot-verification.json.

The startup guard refuses execution without enforced CPU/memory limits.
User-service lifetime follows the user manager; unattended startup without a
login may require linger, which has not been enabled by this work.

## Audit append and recovery

Token and SSMT audit writers use a common flock-serialized append path. Each
append recomputes the entire existing chain, validates sequence numbers where
present, and compares count/tail with a separate durable checkpoint. The lock
covers verification, append, fsync and checkpoint replacement. Snapshot names
and SSMT object IDs now include a unique filename component.

The checkpoint is external to the JSONL, in the same advisory storage directory.
It detects log-only corruption, rewrite, truncation and stale writers. It is NOT
an independent security principal: an actor able to rewrite both log and
checkpoint is outside this protection. Preserve independently trusted checkpoint
copies for stronger rollback detection.

Existing nonempty chains without checkpoints fail closed. Explicit migration is
available through ph6.advisory_chain.anchor_existing with independently verified
expected_count and expected_tail. Never compute a new tip from suspect bytes and
call that trusted. No pre-existing evidence was auto-anchored by this work.

A crash between durable log append and checkpoint update stops further appends.
Preserve both artifacts, independently reconcile the tail, and make a reviewed
recovery decision; do not delete/recreate checkpoints to suppress errors.
Checkpoint verification also runs before token-store loading. This is not a new
full reconstruction of materialized token snapshots. Separate TokenStore
instances can still race in their materialized snapshot writes; use one owner.

Verification currently scans the whole audit chain on each append: cost grows
with history length. The SSMT process isolates this cost from capture; primary
TOK bookkeeping is still synchronous. Bounded segments/checkpoint rotation need
a separate design before sustained high-volume operation.

## Lifecycle scope

Existing VDT/VLT pruning, archival and reload behavior remains. No 30-day purge
or automatic deletion was enabled. CRAM-A and CRAM-R remain untouched. This work
does not add missing live VDT/VLT producers, BCV2 integration, or a new anchor-pack
rehydration system.

Provenance: proposed_by=codex-lane2; proposed_at=2026-09-19; ratified_by=null.
