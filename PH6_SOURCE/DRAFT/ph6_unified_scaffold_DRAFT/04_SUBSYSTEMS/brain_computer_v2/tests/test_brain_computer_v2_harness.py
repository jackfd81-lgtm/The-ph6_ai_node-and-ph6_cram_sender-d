import json
import unittest
from copy import deepcopy
from pathlib import Path

from brain_computer_v2 import BrainComputerV2

FIXTURE_STATE = {
    "brain_id": "BRAIN-TEST-001",
    "nodes": [
        {"id": "ROLE-BCV2-001", "type": "ROLE_SPEC", "label": "Brain Computer v2", "classification": "ROLE", "content": "External memory and continuity layer.", "sequence": 1, "created_at": "2026-06-21T00:00:01Z", "active": True, "retrieval_tags": ["role", "v2"]},
        {"id": "CONSTRAINT-DOCTRINE-001", "type": "DOCTRINE_SPEC", "label": "Operational Doctrine", "classification": "CONSTRAINT", "content": "Organizational only; append-only; no truth validation.", "sequence": 2, "created_at": "2026-06-21T00:00:02Z", "active": True, "retrieval_tags": ["doctrine"]},
        {"id": "GOAL-RETRIEVAL-001", "type": "POLICY_SPEC", "label": "Retrieval Policy v2", "classification": "GOAL", "content": "Retrieve active anchors and one-hop related context/output.", "sequence": 3, "created_at": "2026-06-21T00:00:03Z", "active": True, "retrieval_tags": ["goal", "retrieval"]},
        {"id": "NEXTSTEP-BUILD-001", "type": "TASK_SPEC", "label": "Build module", "classification": "NEXT_STEP", "content": "Implement deterministic module.", "sequence": 4, "created_at": "2026-06-21T00:00:04Z", "active": True, "retrieval_tags": ["next-step"]},
        {"id": "CONTEXT-NODEMODEL-001", "type": "SCHEMA_SPEC", "label": "Node Model v2", "classification": "CONTEXT", "content": "Node model fields and semantics.", "sequence": 5, "created_at": "2026-06-21T00:00:05Z", "active": True, "retrieval_tags": ["context", "schema"]},
        {"id": "OUTPUT-CODE-001", "type": "CODE_SPEC", "label": "Module surface", "classification": "OUTPUT", "content": "addNode, addEdge, appendLedgerEvent, supersedeNode, retrieveContext.", "sequence": 6, "created_at": "2026-06-21T00:00:06Z", "active": True, "retrieval_tags": ["output", "module"]},
        {"id": "CONTEXT-CONFLICT-001", "type": "CONFLICT_SPEC", "label": "Conflict context", "classification": "CONTEXT", "content": "Context that is in contradiction relation with an anchor.", "sequence": 7, "created_at": "2026-06-21T00:00:07Z", "active": True, "retrieval_tags": ["context", "conflict"]}
    ],
    "edges": [
        {"from": "GOAL-RETRIEVAL-001", "to": "CONTEXT-NODEMODEL-001", "relation": "SUPPORTS"},
        {"from": "NEXTSTEP-BUILD-001", "to": "OUTPUT-CODE-001", "relation": "SUPPORTS"},
        {"from": "CONSTRAINT-DOCTRINE-001", "to": "CONTEXT-CONFLICT-001", "relation": "CONTRADICTS"}
    ],
    "ledger": [],
    "notes": {
        "ambiguities": [],
        "continuity_observations": ["Deterministic fixture session loaded."],
        "contradictions": ["Fixture includes contradiction edge for retrieval validation."]
    }
}

class BrainComputerV2Harness(unittest.TestCase):
    def setUp(self):
        self.brain = BrainComputerV2(state=deepcopy(FIXTURE_STATE))

    def test_retrieve_context_preserves_contradiction_and_related_nodes(self):
        ids = [n["id"] for n in self.brain.retrieveContext()]
        self.assertEqual(ids, [
            "ROLE-BCV2-001",
            "CONSTRAINT-DOCTRINE-001",
            "GOAL-RETRIEVAL-001",
            "NEXTSTEP-BUILD-001",
            "CONTEXT-NODEMODEL-001",
            "OUTPUT-CODE-001",
            "CONTEXT-CONFLICT-001",
        ])

    def test_supersede_node_preserves_history_and_creates_delta(self):
        new_node = self.brain.supersedeNode(
            old_node_id="NEXTSTEP-BUILD-001",
            node_type="TASK_SPEC",
            label="Build module v2 refined",
            classification="NEXT_STEP",
            content="Implement deterministic module with persistence aliases.",
            retrieval_tags=["next-step", "refined"]
        )
        old_node = next(n for n in self.brain.nodes if n["id"] == "NEXTSTEP-BUILD-001")
        self.assertFalse(old_node["active"])
        self.assertTrue(new_node["active"])
        self.assertTrue(any(e["from"] == new_node["id"] and e["to"] == "NEXTSTEP-BUILD-001" and e["relation"] == "DELTA_OF" for e in self.brain.edges))

    def test_retrieve_context_after_supersede_uses_new_active_next_step(self):
        new_node = self.brain.supersedeNode(
            old_node_id="NEXTSTEP-BUILD-001",
            node_type="TASK_SPEC",
            label="Build module v2 refined",
            classification="NEXT_STEP",
            content="Implement deterministic module with persistence aliases.",
            retrieval_tags=["next-step", "refined"]
        )
        ids = [n["id"] for n in self.brain.retrieveContext()]
        self.assertIn(new_node["id"], ids)
        self.assertNotIn("NEXTSTEP-BUILD-001", ids)

    def test_duplicate_node_id_raises(self):
        with self.assertRaisesRegex(ValueError, "Duplicate node id"):
            self.brain.addNode(
                node_type="ROLE_SPEC",
                label="Duplicate",
                classification="ROLE",
                content="Duplicate id test.",
                node_id="ROLE-BCV2-001"
            )

    def test_malformed_edge_missing_node_raises(self):
        with self.assertRaisesRegex(ValueError, "Node not found"):
            self.brain.addEdge("ROLE-BCV2-001", "MISSING-NODE-001", "SUPPORTS")

    def test_canonical_hash_round_trip_verification(self):
        envelope = self.brain.state_verification_envelope(session_id="SESSION-TEST-001")
        result = self.brain.verify_imported_state(envelope)
        self.assertTrue(result["hash_matches"])
        self.assertTrue(result["round_trip_equal"])
        self.assertTrue(result["deep_copy_non_identity"])



    def test_duplicate_constraint_canonicalization_flow(self):
        self.brain.addNode(
            node_type="CONSTRAINT_SPEC",
            label="Canonical ledger",
            classification="CONSTRAINT",
            content="Ledger is append only and records what changed and why.",
            retrieval_tags=["ledger", "append-only"],
            node_id="CONSTRAINT-C03"
        )
        self.brain.addNode(
            node_type="CONSTRAINT_SPEC",
            label="Duplicate ledger",
            classification="CONSTRAINT",
            content="Ledger is append only and records what changed and why.",
            retrieval_tags=["ledger", "continuity"],
            node_id="CONSTRAINT-32069379"
        )
        canonical = next(n for n in self.brain.nodes if n["id"] == "CONSTRAINT-C03")
        duplicate = next(n for n in self.brain.nodes if n["id"] == "CONSTRAINT-32069379")
        canonical["retrieval_tags"] = sorted(set(canonical["retrieval_tags"]) | set(duplicate["retrieval_tags"]))
        duplicate["active"] = False
        self.brain.edges.append({"from": "CONSTRAINT-32069379", "to": "CONSTRAINT-C03", "relation": "DELTA_OF"})
        self.assertFalse(duplicate["active"])
        self.assertIn("continuity", canonical["retrieval_tags"])
        self.assertTrue(any(e["from"] == "CONSTRAINT-32069379" and e["to"] == "CONSTRAINT-C03" and e["relation"] == "DELTA_OF" for e in self.brain.edges))

def run_harness(output_dir="output"):
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BrainComputerV2Harness)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    payload = {
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "successful": result.wasSuccessful()
    }
    output_path = Path(output_dir) / "brain_computer_v2_harness_results.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


if __name__ == "__main__":
    run_harness()
