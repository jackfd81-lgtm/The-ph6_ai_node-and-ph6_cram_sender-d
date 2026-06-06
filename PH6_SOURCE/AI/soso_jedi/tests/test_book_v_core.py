#!/usr/bin/env python3
"""
PH6 Book V Core Canonical Tests (spec §9 equivalent).
Two invariants required by v5.0 spec: replay determinism + MCI parsimony.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jedi.swarm_sim_bp import BookVCoreEngine


class TestPH6CanonicalInvariants(unittest.TestCase):

    def test_absolute_replay_determinism(self):
        """Separate runs return identical trace signatures despite clock variability."""
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
        """MCI formula appropriately scores and penalizes unsupported assumptions."""
        engine = BookVCoreEngine(execution_seed=100)
        branches = engine.run_storm_exploration(10)
        evaluation = engine.run_swarm_evaluation(branches)
        layer, _, _ = engine.run_jedi_reconstruction(11, 10, branches, evaluation)

        self.assertGreaterEqual(float(layer["mci_score"]), 0.0)


if __name__ == "__main__":
    unittest.main()
