"""
ph6.cram_pu._lane1_auth

Runtime Lane-1 commit authorization primitive.

Scope (per PH6-RUNTIME-LANE-1-AUTHORIZATION-BOUNDARY task, 2026-09-15):
this closes the specific, certified stop-ship defect (AI_ADVISORY-003 /
PSEUDO-SEAM-001 / SOSO-SPOOF-001's sibling finding) that both
`AtomicCRAMCommitter.commit()` (cram_pu/tools/cram_pu_atomic_commit.py)
and `CRAMWriter.commit()` (cram_pu/crash_replay.py) accepted any
caller-constructed, PASS-shaped dict with no check that it originated
from a real Lane-1 adjudication path.

Mechanism: a process-local secret (`secrets.token_bytes(32)`, module
scope, never re-exported as a plain name outside this module) keys a
BLAKE2b-256 MAC over the exact fields of a commit request. `mint_commit_authorization`
and `verify_commit_authorization` are the only public names; neither
exposes the secret itself.

Deliberate minimality (not the full PH6-AUTH-BOUNDARY-001-DESIGN.md
capability scheme): this repository has NO single shared adjudication
function all production CRAMWriter/AtomicCRAMCommitter callers funnel
through today (VerdictLogger.log() is used by some callers; others --
e.g. life_cram_lcc_01_live_camera.py, the run_c09/c10-c12/c13 campaign
tools -- compute a verdict inline and call commit() directly). Binding
authorization to "this exact adjudication function executed" therefore
cannot be made to work for every existing legitimate caller without
retrofitting each one's verdict-computation logic separately, which
would not be the minimum necessary change. This mechanism instead binds
authorization to "minted by code that imports this module" -- i.e. code
that already lives inside the Lane-1 `ph6.cram_pu` package tree. The
Lane-2 advisory package elsewhere in this repository already has a
separate, statically-tested rule (its own reverse-path test suite)
forbidding any of its non-test modules from importing anything under
`ph6.cram_pu` at all, so none of that Lane-2 code can reach this module
either -- this mechanism relies on that existing, independently-enforced
direction rather than re-stating it here by name.

RESIDUAL RISK, stated explicitly (same limits PH6-AUTH-BOUNDARY-001-DESIGN.md
Part 1 Section 2 already states for its own closure-secret design): this
is an in-process integrity mechanism, not a cryptographic isolation
boundary against code with equal process privilege. It fully closes the
demonstrated attack (an external script, or any module outside
`ph6.cram_pu`, constructing a commit request from scratch) because such
code has no import path to `mint_commit_authorization` and therefore
cannot produce a valid MAC. It does NOT defend against code physically
added to a file inside `ph6/cram_pu/` itself -- that remains a
source-integrity/code-review concern (git history, PR review, "never
commit without operator approval"), out of scope for a runtime
mechanism, exactly as the original design document states for its own
proposal.

Sequence/replay binding (PH6-AUTH-BOUNDARY-001-DESIGN.md Part 2B/3.1's
unresolved `mint_seq` question for CRAMWriter, which has no `_seq`
counter) is deliberately NOT implemented here. `frame_id` /
`packet_id` are already part of the MAC'd field set and are already the
existing per-commit identity key for each class (CRAMWriter's own
file-naming scheme, `AtomicCRAMCommitter`'s `packet_id`), so a mint for
one frame/packet cannot be replayed against a different one -- this
closes cross-payload replay. Replay of a still-valid authorization
against the *same* frame_id/packet_id twice is not separately defended
against beyond what already exists (a second commit for an
already-committed frame_id overwrites the same filename with byte-
identical content, since the fields -- and therefore the MAC -- must
match exactly); this is recorded as a known, intentionally out-of-scope
limitation rather than silently assumed solved, per the task's own
instruction not to guess at unresolved design questions.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any, Dict

from ph6.cram_pu.schemas.canonical import canonical_json

AUTHORIZATION_SCHEMA = "ph6.lane1_commit_authorization.v1"

_SECRET = secrets.token_bytes(32)


class LaneOneAuthorizationError(Exception):
    """Raised when a commit request cannot establish valid Lane-1 authorization.

    Raised before any filesystem I/O for the commit in question -- no
    CRAM-A artifact, partial file, or marker is ever produced when this
    is raised.
    """


def _mac(fields: Dict[str, Any]) -> str:
    return hashlib.blake2b(canonical_json(fields), digest_size=32, key=_SECRET).hexdigest()


def mint_commit_authorization(**fields: Any) -> Dict[str, Any]:
    """
    Mint an authorization object binding exactly `fields` (the commit
    request's identity: frame_id/packet_id, payload_hash, verdict, ...).
    Only code that can import this module (i.e. code inside
    ph6.cram_pu) can call this -- no Lane-2 advisory or AI/research_agent
    path elsewhere in this repository has an import path here, per that
    tree's own statically-tested reverse-path isolation rule.
    """
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "fields": dict(fields),
        "mac": _mac(fields),
    }


def verify_commit_authorization(authorization: Any, **expected_fields: Any) -> None:
    """
    Raise LaneOneAuthorizationError unless `authorization` is a well-formed
    object minted by this module for exactly `expected_fields`. Fails
    closed on: missing/None authorization, wrong schema, mismatched
    fields (binds authorization to *this specific* commit request, not
    merely *a* valid-looking one), or a MAC that does not verify against
    the live process secret (constant-time comparison).
    """
    if not isinstance(authorization, dict):
        raise LaneOneAuthorizationError(
            "Lane-1 commit authorization missing or malformed: expected a dict, "
            f"got {type(authorization).__name__}"
        )
    if authorization.get("schema") != AUTHORIZATION_SCHEMA:
        raise LaneOneAuthorizationError(
            f"Lane-1 commit authorization has wrong/missing schema: "
            f"{authorization.get('schema')!r}"
        )
    if authorization.get("fields") != dict(expected_fields):
        raise LaneOneAuthorizationError(
            "Lane-1 commit authorization fields do not match this commit request "
            "(authorization was not minted for this exact frame_id/payload_hash/verdict)"
        )
    mac = authorization.get("mac")
    if not isinstance(mac, str) or not hmac.compare_digest(mac, _mac(authorization["fields"])):
        raise LaneOneAuthorizationError(
            "Lane-1 commit authorization MAC does not verify against the live "
            "process secret -- forged, tampered, or minted by a different process"
        )
