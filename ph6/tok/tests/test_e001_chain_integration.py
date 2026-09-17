"""
E001 integration chain + PM-02 four-experience bench.

Exercises the full advisory chain this LMPQ-001 work item targets:

    Reality (synthetic frame bytes)
      -> CRAM-0 preservation (CRAMWriter, real Lane-1 code)
      -> PSEUDO-M (deterministic fixed-point metrics)
      -> PSEUDO-A (PASS/DROP authority — the only PASS/DROP source here)
      -> RT (Lane-2 advisory reference token)
      -> RLT / AHT (loss detection + anchor, on simulated evidence loss)
      -> AHT -> RT rehydration
      -> SoSo-JEDI single-token provenance lookup (Lane-2, ADVISORY_ZERO)
      -> verified source hash (closes the loop back to Lane-1 evidence)

This module is a test-only demonstration harness. It is not a Lane-1
component, issues no PASS/DROP of its own, and its "PSEUDO-M"/"PSEUDO-A"
helpers below are a minimal synthetic stand-in for the real fixed-point
metric/verdict functions already implemented in
ph6/cram_pu/tools/life_cram_lcc_01_live_camera.py — reproduced here in
trivial form only so this test has no camera/OpenCV dependency.

PM-02 requires >=4 deliberately different experiences. The four below are:
  1. normal successful path (PASS -> RT)
  2. DROP path (no CRAM commit, no RT) + loss path (RT -> RLT/AHT)
  3. rehydration path (AHT -> new RT)
  4. provenance/continuity path (SoSo-JEDI single-token lookup)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from ph6.cram_pu.arrival_logger import ArrivalLogger
from ph6.cram_pu.crash_replay import CRAMWriter
from ph6.cram_pu.departure_logger import DepartureLogger
from ph6.tok.evidence import attempt_rehydration, detect_rt_loss
from ph6.tok.lifecycle import RT, TokenStore

_SOSO_JEDI_ROOT = (
    Path(__file__).resolve().parents[3] / "PH6_SOURCE" / "AI" / "soso_jedi"
)
sys.path.insert(0, str(_SOSO_JEDI_ROOT))
from token_provenance import build_token_provenance  # noqa: E402


def _pseudo_measure(payload: bytes) -> dict:
    """PSEUDO-M analog: deterministic fixed-point metrics over raw bytes.
    Synthetic (no image decode) — same discipline as the real camera
    metrics function: pure, deterministic, fixed-point only. Byte-diversity
    is used as an entropy proxy purely so this test can craft payloads
    with a predictable PASS/DROP outcome; it makes no claim about real
    image entropy."""
    unique_bytes = len(set(payload))
    entropy_proxy_fp = unique_bytes * 100
    return {"entropy_proxy_fp": entropy_proxy_fp, "size_bytes": len(payload)}


def _pseudo_adjudicate(metrics: dict) -> tuple[str, list[str]]:
    """PSEUDO-A analog: PASS/DROP only, no weighting, no confidence."""
    reasons = []
    if metrics["entropy_proxy_fp"] < 500:
        reasons.append("entropy_proxy_too_low")
    if metrics["size_bytes"] < 4:
        reasons.append("payload_too_small")
    return ("PASS" if not reasons else "DROP"), reasons


def _ingest_frame(paths, cram_writer, frame_id: int, payload: bytes):
    """Runs one frame through the full Lane-1 ingest chain and returns
    (verdict, payload_hash, cram_commit_or_none)."""
    dep = DepartureLogger(paths["departure_log"]).log(frame_id, payload)
    arr = ArrivalLogger(paths["arrival_log"]).log(frame_id, payload, dep["payload_hash"])
    assert arr["transfer_status"] == "OK"

    metrics = _pseudo_measure(payload)
    verdict, reasons = _pseudo_adjudicate(metrics)

    commit = None
    if verdict == "PASS":
        commit = cram_writer.commit(frame_id, dep["payload_hash"], {"verdict": "PASS", "frame_id": frame_id})

    return verdict, reasons, dep["payload_hash"], commit


def _setup(tmp_path) -> dict:
    cram_store = tmp_path / "cram_store"
    cram_store.mkdir(parents=True, exist_ok=True)
    (cram_store / "payloads").mkdir(exist_ok=True)
    return {
        "cram_store": cram_store,
        "departure_log": cram_store / "departure_log.jsonl",
        "arrival_log": cram_store / "arrival_log.jsonl",
    }


def test_e001_four_experience_bench(tmp_path):
    paths = _setup(tmp_path)
    cram_writer = CRAMWriter(paths["cram_store"])
    store = TokenStore(str(tmp_path / "mram-s" / "tokens"))

    all_token_records: list[dict] = []

    # ------------------------------------------------------------------
    # Experience 1 — normal successful path: PASS -> RT
    # ------------------------------------------------------------------
    frame_1 = b"E001-EXPERIENCE-1-NORMAL-SUCCESSFUL-PAYLOAD"
    verdict_1, reasons_1, payload_hash_1, commit_1 = _ingest_frame(
        paths, cram_writer, frame_id=1, payload=frame_1
    )
    assert verdict_1 == "PASS", reasons_1
    assert commit_1 is not None
    assert commit_1["authority"] == "LANE_1"

    (paths["cram_store"] / "payloads" / "frame_0000000001.bin").write_bytes(frame_1)

    rt_1 = RT(
        token_id="rt_exp1", cram_ref_hash=payload_hash_1, timestamp_ms=1_000,
        object_class="experience_1",
    )
    store.add_rt(rt_1)
    all_token_records.append(rt_1.to_dict())

    # Evidence for experience 1 stays intact — the E2/E3 loss+rehydration
    # story below is deliberately run on a *different* frame so E1 remains
    # the clean "nothing went wrong" baseline.
    intact_check = detect_rt_loss(store, rt_1, paths["cram_store"], frame_id=1, event_time_ms=1_100)
    assert intact_check is None

    # ------------------------------------------------------------------
    # Experience 2 — DROP path (no CRAM commit, no RT) + loss path
    # (RT -> RLT/AHT on a separate, previously-PASS frame)
    # ------------------------------------------------------------------
    frame_2_drop = b""  # too small -> PSEUDO-A DROP
    verdict_2, reasons_2, _payload_hash_2, commit_2 = _ingest_frame(
        paths, cram_writer, frame_id=2, payload=frame_2_drop
    )
    assert verdict_2 == "DROP"
    assert commit_2 is None
    assert not (paths["cram_store"] / "cram_0000000002.json").exists()

    frame_2_loss = b"E001-EXPERIENCE-2-FRAME-THAT-WILL-BE-LOST"
    verdict_2b, reasons_2b, payload_hash_2b, commit_2b = _ingest_frame(
        paths, cram_writer, frame_id=3, payload=frame_2_loss
    )
    assert verdict_2b == "PASS", reasons_2b
    (paths["cram_store"] / "payloads" / "frame_0000000003.bin").write_bytes(frame_2_loss)

    rt_2 = RT(token_id="rt_exp2", cram_ref_hash=payload_hash_2b, timestamp_ms=2_000)
    store.add_rt(rt_2)
    all_token_records.append(rt_2.to_dict())

    # Simulate loss: the durable CRAM commit for frame 3 goes missing.
    saved_commit_text = (paths["cram_store"] / "cram_0000000003.json").read_text(encoding="utf-8")
    (paths["cram_store"] / "cram_0000000003.json").unlink()

    rlt_2 = detect_rt_loss(store, rt_2, paths["cram_store"], frame_id=3, event_time_ms=2_100)
    assert rlt_2 is not None
    assert rlt_2.detection_reason == "cram_record_missing"
    all_token_records.append(rlt_2.to_dict())

    aht_2 = store.aht_store[rlt_2.aht_token_id]
    all_token_records.append(aht_2.to_dict())

    # ------------------------------------------------------------------
    # Experience 3 — rehydration path: AHT -> new RT
    # ------------------------------------------------------------------
    (paths["cram_store"] / "cram_0000000003.json").write_text(saved_commit_text, encoding="utf-8")

    rehydrated_rt = attempt_rehydration(
        store, aht_2, paths["cram_store"], frame_id=3,
        expected_payload_hash=payload_hash_2b, event_time_ms=3_000,
    )
    assert rehydrated_rt is not None
    assert rehydrated_rt.metadata["provenance"] == "REHYDRATION"
    assert store.aht_store[aht_2.token_id].rehydration_status == "SUCCEEDED"
    all_token_records.append(rehydrated_rt.to_dict())

    # ------------------------------------------------------------------
    # Experience 4 — provenance / continuity path via SoSo-JEDI adapter
    # ------------------------------------------------------------------
    provenance = build_token_provenance(rehydrated_rt.token_id, all_token_records)

    assert provenance["chain_length"] == 3  # rehydrated RT -> AHT -> lost RT
    assert [c["token_id"] for c in provenance["chain"]] == [
        rehydrated_rt.token_id, aht_2.token_id, rt_2.token_id,
    ]
    assert provenance["authority"] == "ADVISORY_ZERO"
    assert provenance["may_replace_primary_evidence"] is False

    # Provenance must trace back to a real, hash-verified Lane-1 commit —
    # "verified source/hash": recompute frame 3's hash independently and
    # confirm it matches the chain root's cram_ref_hash.
    recomputed_hash = hashlib.blake2b(frame_2_loss, digest_size=32).hexdigest()
    root_cram_ref_hash = provenance["chain"][-1]["cram_ref_hash"]
    assert root_cram_ref_hash == recomputed_hash == payload_hash_2b

    # Determinism / replay isolation: identical input -> identical trace_hash.
    provenance_replay = build_token_provenance(rehydrated_rt.token_id, list(all_token_records))
    assert provenance_replay["trace_hash"] == provenance["trace_hash"]

    # Continuity: experience 1's untouched lineage still resolves trivially.
    e1_provenance = build_token_provenance(rt_1.token_id, [rt_1.to_dict()])
    assert e1_provenance["chain_length"] == 1
