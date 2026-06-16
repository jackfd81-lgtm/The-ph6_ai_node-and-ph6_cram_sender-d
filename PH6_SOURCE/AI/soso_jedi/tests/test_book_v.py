#!/usr/bin/env python3
"""
PH6 Book V test suite.
Tests: replay determinism, MCI bounds, GENESIS chain, chain advance, authority enforcement.
"""
import sys
import unittest
from pathlib import Path

# soso_jedi/ root → enables `from jedi.swarm_sim_bp import ...`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jedi.swarm_sim_bp import BookVCoreEngine


class TestPH6BookV(unittest.TestCase):

    def test_absolute_replay_determinism(self):
        """Two fresh instances with same seed must produce identical hashes regardless of wall-clock."""
        run_a = BookVCoreEngine(execution_seed=2026)
        run_b = BookVCoreEngine(execution_seed=2026)

        branches_a = run_a.run_storm_exploration(base_layer_id=44)
        branches_b = run_b.run_storm_exploration(base_layer_id=44)
        self.assertEqual(branches_a, branches_b)

        eval_a = run_a.run_swarm_evaluation(branches_a)
        eval_b = run_b.run_swarm_evaluation(branches_b)

        layer_a, block_a, advisory_a = run_a.run_jedi_reconstruction(45, 44, branches_a, eval_a)
        layer_b, block_b, advisory_b = run_b.run_jedi_reconstruction(45, 44, branches_b, eval_b)

        self.assertEqual(layer_a["continuity_hash"], layer_b["continuity_hash"])
        self.assertEqual(block_a["continuity_hash"], block_b["continuity_hash"])
        self.assertEqual(advisory_a["trace_hash"], advisory_b["trace_hash"])

    def test_mci_parsimony_bounds(self):
        """MCI score in [0.0, 1.0]; non-zero recovered_nodes keeps score below 1."""
        engine = BookVCoreEngine(execution_seed=100)
        branches = engine.run_storm_exploration(10)
        evaluation = engine.run_swarm_evaluation(branches)
        layer, _, _ = engine.run_jedi_reconstruction(11, 10, branches, evaluation)

        mci = float(layer["mci_score"])
        self.assertGreaterEqual(mci, 0.0)
        # 3 branches → 12 recovered nodes; 2 assumptions → MCI = 2/12 ≈ 0.167
        self.assertLess(mci, 1.0)

    def test_genesis_chain_start(self):
        """Fresh engine begins with GENESIS prev_hash for both chain types."""
        engine = BookVCoreEngine()
        branches = engine.run_storm_exploration(0)
        evaluation = engine.run_swarm_evaluation(branches)
        _, block, advisory = engine.run_jedi_reconstruction(1, 0, branches, evaluation)

        self.assertEqual(block["prev_continuity_hash"], "GENESIS")
        self.assertEqual(advisory["prev_trace_hash"], "GENESIS")

    def test_chain_sequence_advances(self):
        """Sequence numbers increment across consecutive reconstructions."""
        engine = BookVCoreEngine(execution_seed=7)
        for i in range(3):
            branches = engine.run_storm_exploration(i)
            evaluation = engine.run_swarm_evaluation(branches)
            _, block, advisory = engine.run_jedi_reconstruction(i + 1, i, branches, evaluation)

        self.assertEqual(block["continuity_seq"], 2)
        self.assertEqual(advisory["trace_seq"], 2)
        self.assertRegex(block["continuity_hash"], r"^[a-f0-9]{64}$")
        self.assertRegex(advisory["trace_hash"], r"^[a-f0-9]{64}$")

    def test_authority_zero_on_all_records(self):
        """Every output record must carry authority=ADVISORY_ZERO."""
        engine = BookVCoreEngine()
        branches = engine.run_storm_exploration(0)
        for b in branches:
            self.assertEqual(b["authority"], "ADVISORY_ZERO")
        evaluation = engine.run_swarm_evaluation(branches)
        self.assertEqual(evaluation["authority"], "ADVISORY_ZERO")
        layer, block, advisory = engine.run_jedi_reconstruction(1, 0, branches, evaluation)
        self.assertEqual(layer["authority"], "ADVISORY_ZERO")
        self.assertEqual(block["authority"], "ADVISORY_ZERO")
        self.assertEqual(advisory["authority"], "ADVISORY_ZERO")

    def test_schema_ids_dot_separated(self):
        """Schema IDs must use dot-separation (no underscores in field names)."""
        engine = BookVCoreEngine()
        branches = engine.run_storm_exploration(0)
        evaluation = engine.run_swarm_evaluation(branches)
        layer, block, advisory = engine.run_jedi_reconstruction(1, 0, branches, evaluation)

        self.assertEqual(layer["schema_id"], "ph6.cognitive.stratigraphy.layer.v1")
        self.assertEqual(block["schema_id"], "ph6.soso.continuity_block.v1")
        self.assertEqual(advisory["schema_id"], "ph6.advisory.manifest.v1")

    def test_hash_width_is_64_hex(self):
        """All BLAKE2b-256 hashes must be exactly 64 hex characters."""
        engine = BookVCoreEngine()
        branches = engine.run_storm_exploration(0)
        evaluation = engine.run_swarm_evaluation(branches)
        layer, block, advisory = engine.run_jedi_reconstruction(1, 0, branches, evaluation)

        for h in [layer["continuity_hash"], block["continuity_hash"], advisory["trace_hash"]]:
            self.assertEqual(len(h), 64, f"Hash width != 64: {h!r}")
            self.assertRegex(h, r"^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main()
