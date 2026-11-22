"""
ph6.jedi_master_evidence_bridge

Lane: 1-adjacent (reads Lane-1 CRAM-A only; never writes, never adjudicates)
Authority: NONE

Deliberately placed at the top of the ph6/ tree, NOT inside ph6/cram_pu/
and NOT inside ph6_l2_expand/ -- both trees have their own statically
enforced, bidirectional isolation walls that this module would trip if
placed on either side:

  - ph6_l2_expand/tests/test_no_reverse_path.py: no module under
    ph6_l2_expand may import ph6.cram_pu, ph6.ph6_cert, or ph6.audit.
  - ph6_l2_expand/tests/test_replay_independence.py and
    test_soso_tokens_not_lane1.py: no file under ph6/cram_pu may even
    mention "ph6_l2_expand" (deleting ph6_l2_expand must never break
    cram_pu).

So this is the ONLY place a JEDI Master caller may touch
ph6.cram_pu.evidence_boundary. Whatever drives JEDI Master (a CLI, a
test, an operator script) calls fetch_evidence_views() here first and
passes the resulting plain-dict data into
ph6_l2_expand.jedi_master.master.run_advisory_task(evidence_views=...).
ph6_l2_expand.jedi_master.deterministic_prep never calls
PH6EvidenceAccessBoundary itself.

Converts each EvidenceView to a plain dict (str status, no enum, no
dataclass) so nothing Lane-1-typed crosses into ph6_l2_expand.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

from ph6.cram_pu.crash_replay import CRAMPaths
from ph6.cram_pu.evidence_boundary import PH6EvidenceAccessBoundary


def fetch_evidence_views(cram_paths: CRAMPaths, frame_ids: Iterable[int]) -> Dict[int, Optional[dict]]:
    """
    Returns {frame_id: view_dict_or_None}. view_dict_or_None is None only
    when the frame_id itself was invalid (e.g. negative, non-int) --
    NOT_FOUND / CONFLICT are still returned as a dict so the caller can
    see *why* a reference didn't resolve, exactly as EvidenceView already
    distinguishes them; this bridge relabels nothing.
    """
    boundary = PH6EvidenceAccessBoundary(cram_paths)
    out: Dict[int, Optional[dict]] = {}
    for frame_id in frame_ids:
        view = boundary.get_evidence(frame_id)
        if view.frame_id is None:
            out[frame_id] = None
            continue
        out[view.frame_id] = {
            "status": view.status.value,
            "frame_id": view.frame_id,
            "cram_hash": view.cram_hash,
            "prev_cram_hash": view.prev_cram_hash,
        }
    return out


# {"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-09-15T21:56:00Z","api_call_log_ref":"session-jedi-master-build-20260915","ratified_by":null}
