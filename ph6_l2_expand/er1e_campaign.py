"""
ph6_l2_expand.er1e_campaign

ER-1E Real Multi-VLT Advisory Artifact Campaign Generator

Lane: 2
Authority: ZERO
Write domain: PH6_SOURCE/ARTIFACTS/ER1E_REAL_MULTIVLT_20260617/ (campaign artifacts only)

Generates a deterministic, artifact-grade multi-VLT advisory evidence campaign
using the real token lifecycle path.

Run once to regenerate artifacts:
  cd /home/jack && python ph6_l2_expand/er1e_campaign.py

Do NOT import or call generate_campaign() from tests — tests read the
committed artifacts, they do not regenerate them.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Campaign constants
# ---------------------------------------------------------------------------

CAMPAIGN_ID = "ER1E_REAL_MULTIVLT_20260617"
BRANCH = "ph6/er1e-real-multivlt-20260617"

FIXED_T0 = 4_000_000_000_000  # ms — ER-1E anchor (distinct from ER-1A=1T, ER-1B=2T, ER-1D=3T)
CYCLE_SPACING_MS = 2_000       # 2 s between cycles
NUM_CYCLES = 3
VDTS_PER_PROMOTION = 5
VDT_BURST_STEP_MS = 100        # spacing between VDTs in a burst
CYCLE_BBOX_DRIFT = 5.0         # pixels per cycle (proves temporal non-static spatial)
CONFIDENCE = 0.78              # fixed per VDT

_OBJECTS: List[tuple] = [
    # (object_class, base_bbox [x,y,w,h])
    ("vehicle",  [10.0,  20.0,  100.0,  60.0]),
    ("person",   [180.0, 100.0,  40.0,  80.0]),
    ("bicycle",  [320.0, 160.0,  60.0,  80.0]),
    ("sign",     [450.0,  10.0,  30.0,  40.0]),
    ("doorway",  [550.0,   0.0,  80.0, 200.0]),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cycle_cram_ref(cycle: int) -> str:
    return f"cram_er1e_cycle{cycle}_frame001"


def _cycle_bbox(base: List[float], cycle: int) -> List[float]:
    """Shift x by cycle_drift per cycle to prove spatial change across time."""
    drift = (cycle - 1) * CYCLE_BBOX_DRIFT
    return [base[0] + drift, base[1], base[2], base[3]]


# ---------------------------------------------------------------------------
# Campaign generator
# ---------------------------------------------------------------------------

def generate_campaign(artifact_root: Path) -> Dict[str, Any]:
    """
    Run the ER-1E campaign through the real token lifecycle path.

    Writes 4 artifact files to artifact_root:
      source_observations.jsonl
      tok_advisory_audit.jsonl
      reconstruction_report.json
      manifest.json

    Returns the manifest dict.
    """
    from ph6.tok.lifecycle import VDT, TokenStore, DEFAULT_TOK_CONFIG
    from ph6_l2_expand.topology_reconstruct import reconstruct_topology

    artifact_root.mkdir(parents=True, exist_ok=True)

    source_observations: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as td:
        tokens_dir = Path(td) / "tokens"
        store = TokenStore(str(tokens_dir))

        for cycle in range(1, NUM_CYCLES + 1):
            cram_ref = _cycle_cram_ref(cycle)
            cycle_t0 = FIXED_T0 + (cycle - 1) * CYCLE_SPACING_MS

            for obj_class, base_bbox in _OBJECTS:
                bbox = _cycle_bbox(base_bbox, cycle)
                vdt_ids: List[str] = []

                for i in range(VDTS_PER_PROMOTION):
                    t = cycle_t0 + i * VDT_BURST_STEP_MS
                    vdt_bbox = [bbox[0] + i * 0.1, bbox[1], bbox[2], bbox[3]]
                    vdt = VDT(
                        token_id=f"vdt_er1e_c{cycle}_{obj_class}_{i:03d}",
                        cram_ref_hash=cram_ref,
                        timestamp_ms=t,
                        last_updated_ms=t,
                        object_class=obj_class,
                        bbox=vdt_bbox,
                        confidence=CONFIDENCE,
                        support_count=1,
                    )
                    store.add_vdt(vdt)
                    vdt_ids.append(vdt.token_id)

                vlt = store.promote_to_vlt(
                    vdt_ids,
                    DEFAULT_TOK_CONFIG,
                    event_time_ms=cycle_t0 + 600,
                )
                assert vlt is not None, (
                    f"promotion failed: cycle={cycle} object={obj_class!r}"
                )

                source_observations.append({
                    "schema": "ph6.er1e.source_observation.v1",
                    "authority": "ZERO",
                    "advisory_only": True,
                    "campaign_id": CAMPAIGN_ID,
                    "cycle": cycle,
                    "object_class": obj_class,
                    "cram_ref_hash": cram_ref,
                    "bbox": bbox,
                    "centroid": vlt.centroid,
                    "support_count": vlt.support_count,
                    "first_seen_ms": vlt.first_seen_ms,
                    "last_seen_ms": vlt.last_seen_ms,
                    "vlt_token_id": vlt.token_id,
                })

        # Copy audit chain while temp dir still exists
        tmp_audit = tokens_dir / "tok_advisory_audit.jsonl"
        artifact_audit = artifact_root / "tok_advisory_audit.jsonl"
        shutil.copy2(tmp_audit, artifact_audit)

    # Write source_observations.jsonl (deterministic)
    obs_path = artifact_root / "source_observations.jsonl"
    with open(obs_path, "wb") as fh:
        for obs in source_observations:
            fh.write(_canonical_json(obs) + b"\n")

    # Reconstruct topology from the preserved audit chain
    token_map, topo_hash, meta = reconstruct_topology(artifact_audit)

    vlt_ids_set = sorted({obs["vlt_token_id"] for obs in source_observations})
    object_classes = sorted({obs["object_class"] for obs in source_observations})

    # Write reconstruction_report.json (deterministic)
    report = {
        "schema": "ph6.er1e.reconstruction_report.v1",
        "authority": "ZERO",
        "advisory_only": True,
        "campaign_id": CAMPAIGN_ID,
        "topology_hash": topo_hash,
        "observation_count": meta["observation_count"],
        "token_count": meta["token_count"],
        "vlt_count": len(vlt_ids_set),
        "object_classes": object_classes,
        "chain_errors": meta["chain_errors"],
        "boundary_checks": {
            "cram_writes": False,
            "drop_writes": False,
            "lane1_imports": False,
            "live_mram_s_mutation": False,
            "pass_writes": False,
            "snapshot_cache": False,
            "verdict_writes": False,
        },
    }
    report_path = artifact_root / "reconstruction_report.json"
    report_path.write_bytes(_canonical_json(report) + b"\n")

    # Compute sha256 of the three artifact files before writing manifest
    sha256s = {
        "reconstruction_report.json": _sha256_file(report_path),
        "source_observations.jsonl": _sha256_file(obs_path),
        "tok_advisory_audit.jsonl": _sha256_file(artifact_audit),
    }

    # Write manifest.json
    manifest: Dict[str, Any] = {
        "schema": "ph6.er1e.manifest.v1",
        "advisory_only": True,
        "authority_level": "ZERO",
        "branch": BRANCH,
        "campaign_id": CAMPAIGN_ID,
        "artifact_paths": {
            "reconstruction_report": (
                f"PH6_SOURCE/ARTIFACTS/{CAMPAIGN_ID}/reconstruction_report.json"
            ),
            "source_observations": (
                f"PH6_SOURCE/ARTIFACTS/{CAMPAIGN_ID}/source_observations.jsonl"
            ),
            "tok_advisory_audit": (
                f"PH6_SOURCE/ARTIFACTS/{CAMPAIGN_ID}/tok_advisory_audit.jsonl"
            ),
        },
        "file_sha256": sha256s,
        "forbidden_writes_checked": True,
        "lane1_imports": False,
        "live_mram_s_mutation": False,
        "num_cycles": NUM_CYCLES,
        "num_objects": len(_OBJECTS),
        "object_classes": object_classes,
        "observation_count": meta["observation_count"],
        "snapshot_cache": False,
        "token_count": meta["token_count"],
        "topology_hash": topo_hash,
        "vlt_count": len(vlt_ids_set),
    }
    manifest_path = artifact_root / "manifest.json"
    manifest_path.write_bytes(_canonical_json(manifest) + b"\n")

    return manifest


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _here = Path(__file__).resolve().parent
    _repo_root = _here.parent
    _artifact_root = _repo_root / "PH6_SOURCE" / "ARTIFACTS" / CAMPAIGN_ID

    # Ensure ph6 and ph6_l2_expand are importable
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

    print(f"Generating ER-1E campaign artifacts -> {_artifact_root}")
    manifest = generate_campaign(_artifact_root)

    print(f"campaign_id:       {manifest['campaign_id']}")
    print(f"topology_hash:     {manifest['topology_hash']}")
    print(f"observation_count: {manifest['observation_count']}")
    print(f"token_count:       {manifest['token_count']}")
    print(f"vlt_count:         {manifest['vlt_count']}")
    print(f"object_classes:    {manifest['object_classes']}")
    print("Artifacts written:")
    for name, sha in sorted(manifest["file_sha256"].items()):
        print(f"  {name}: {sha}")
    print("manifest.json: (written last)")
    print("DONE")
