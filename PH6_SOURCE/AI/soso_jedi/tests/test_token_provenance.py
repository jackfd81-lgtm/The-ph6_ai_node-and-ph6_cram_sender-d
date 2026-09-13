#!/usr/bin/env python3
"""
Tests for the single-token provenance adapter (token_provenance.py).

Covers: positive lineage walk, deterministic replay of trace_hash, and the
negative paths the adapter must reject rather than silently paper over —
unknown token_id, broken parent linkage, and lineage cycles.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from token_provenance import AUTHORITY, build_token_provenance


def _rt(token_id, cram_ref_hash):
    return {"token_id": token_id, "token_type": "RT", "cram_ref_hash": cram_ref_hash}


def _rlt(token_id, lost_token_id, cram_ref_hash):
    return {
        "token_id": token_id, "token_type": "RLT",
        "lost_token_id": lost_token_id, "cram_ref_hash": cram_ref_hash,
    }


def _aht(token_id, anchor_for_token_id, cram_ref_hash):
    return {
        "token_id": token_id, "token_type": "AHT",
        "anchor_for_token_id": anchor_for_token_id, "cram_ref_hash": cram_ref_hash,
    }


def _rehydrated_rt(token_id, from_aht_token_id, lost_token_id, cram_ref_hash):
    return {
        "token_id": token_id, "token_type": "RT", "cram_ref_hash": cram_ref_hash,
        "metadata": {
            "rehydrated_from_aht": from_aht_token_id,
            "rehydrated_from_lost_token": lost_token_id,
            "provenance": "REHYDRATION",
        },
    }


class TestTokenProvenanceAdapter(unittest.TestCase):

    def test_single_root_token_chain_of_one(self):
        records = [_rt("rt_1", "a" * 64)]
        result = build_token_provenance("rt_1", records)
        self.assertEqual(result["chain_length"], 1)
        self.assertEqual(result["root_token_type"], "RT")
        self.assertEqual(result["authority"], AUTHORITY)
        self.assertFalse(result["may_replace_primary_evidence"])

    def test_full_loss_rehydration_lineage_walk(self):
        """rehydrated RT -> AHT -> lost RT is the full provenance chain a
        real TOK loss/rehydration cycle would hand to this adapter (the
        version edge is AHT -> RT per doctrine, so AHT is a real hop)."""
        records = [
            _rt("rt_orig", "a" * 64),
            _rlt("rlt_1", "rt_orig", "a" * 64),
            _aht("aht_1", "rt_orig", "a" * 64),
            _rehydrated_rt("rt_new", "aht_1", "rt_orig", "a" * 64),
        ]
        result = build_token_provenance("rt_new", records)
        self.assertEqual(result["chain_length"], 3)
        self.assertEqual(
            [c["token_id"] for c in result["chain"]], ["rt_new", "aht_1", "rt_orig"]
        )
        self.assertEqual(result["root_token_type"], "RT")

    def test_trace_hash_deterministic_across_independent_calls(self):
        records = [_rt("rt_1", "b" * 64), _rlt("rlt_1", "rt_1", "b" * 64)]
        result_a = build_token_provenance("rlt_1", records)
        result_b = build_token_provenance("rlt_1", list(records))  # fresh list object
        self.assertEqual(result_a["trace_hash"], result_b["trace_hash"])

    def test_unknown_token_id_rejected(self):
        with self.assertRaises(ValueError):
            build_token_provenance("does_not_exist", [_rt("rt_1", "c" * 64)])

    def test_broken_parent_link_rejected_not_truncated(self):
        # rlt_1 claims rt_missing as its lost token, but rt_missing is
        # absent from the supplied records — this must fail loudly,
        # never silently stop at rlt_1 and call it a complete chain.
        records = [_rlt("rlt_1", "rt_missing", "d" * 64)]
        with self.assertRaises(ValueError):
            build_token_provenance("rlt_1", records)

    def test_lineage_cycle_rejected(self):
        records = [
            {"token_id": "t1", "token_type": "RLT", "lost_token_id": "t2"},
            {"token_id": "t2", "token_type": "RLT", "lost_token_id": "t1"},
        ]
        with self.assertRaises(ValueError):
            build_token_provenance("t1", records)

    def test_adapter_never_emits_pass_drop_or_verdict_fields(self):
        records = [_rt("rt_1", "e" * 64)]
        result = build_token_provenance("rt_1", records)
        for forbidden in ("verdict", "pass", "drop", "result"):
            self.assertNotIn(forbidden, result)

    def test_adapter_module_performs_no_filesystem_io(self):
        """This adapter must remain a pure function over caller-supplied
        data — it must never read CRAM, MRAM-S, or any other path itself."""
        source = (Path(__file__).resolve().parent.parent / "token_provenance.py").read_text(
            encoding="utf-8"
        )
        forbidden_io_calls = ("open(", ".write_text(", ".write_bytes(", ".mkdir(", "os.open(")
        for call in forbidden_io_calls:
            self.assertNotIn(call, source, f"unexpected I/O call {call!r} in token_provenance.py")


if __name__ == "__main__":
    unittest.main()
