from .swarm_base import BaseSwarm
from .models import SwarmInput


class S1ActiveMemorySwarm(BaseSwarm):
    swarm_id = "S1"
    role = "active_memory"
    ttl_seconds = 30

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "active_cram_refs": list(data.cram_refs),
            "active_tok_refs": list(data.tok_refs),
            "summary": "current advisory state snapshot",
            "_confidence_fp": 95,
        }


class S2ContextAnchorSwarm(BaseSwarm):
    swarm_id = "S2"
    role = "context_anchor"
    ttl_seconds = 120

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "context_hint": "what this system roughly is",
            "cram_count": len(data.cram_refs),
            "tok_count": len(data.tok_refs),
            "_confidence_fp": 80,
        }


class S3SemanticSummarySwarm(BaseSwarm):
    swarm_id = "S3"
    role = "semantic_summary"
    ttl_seconds = 120

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "summary_type": "structured",
            "ref_count": len(data.cram_refs) + len(data.tok_refs),
            "advisory_refs_consumed": list(data.advisory_refs),
            "_confidence_fp": 85,
        }


class S4ProjectIdentitySwarm(BaseSwarm):
    swarm_id = "S4"
    role = "project_identity"
    ttl_seconds = 3600

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "system": "PH6/CRAM",
            "layer": "LANE_2_ADVISORY",
            "ssmt_role": "swarm cognition advisory",
            "_confidence_fp": 100,
        }


class S5HistoricalAwarenessSwarm(BaseSwarm):
    swarm_id = "S5"
    role = "historical_awareness"
    ttl_seconds = 1800

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "stabilized_patterns": [],
            "long_term_cram_refs": list(data.cram_refs),
            "_confidence_fp": 70,
        }


class S6LatentKnowledgeSwarm(BaseSwarm):
    swarm_id = "S6"
    role = "latent_knowledge"
    ttl_seconds = 7200

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "latent_signals": [],
            "weak_ref_count": len(data.cram_refs),
            "dormant": True,
            "_confidence_fp": 40,
        }


class S7UpdateIntakeSwarm(BaseSwarm):
    swarm_id = "S7"
    role = "update_intake"
    ttl_seconds = 60

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "new_advisory_refs": list(data.advisory_refs),
            "watching": True,
            "_confidence_fp": 90,
        }


class S8DriftTrackingSwarm(BaseSwarm):
    swarm_id = "S8"
    role = "drift_tracking"
    ttl_seconds = 300

    def compute_payload(self, data: SwarmInput) -> dict:
        drift = max(0, 5 - len(data.cram_refs))
        return {
            "drift_detected": drift > 2,
            "conflict_signals": [],
            "_drift_score": drift,
            "_confidence_fp": 75,
        }


class S9FutureAcquisitionSwarm(BaseSwarm):
    swarm_id = "S9"
    role = "future_acquisition"
    ttl_seconds = 600

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "predicted_gaps": [],
            "acquisition_targets": [],
            "future_facing": True,
            "_confidence_fp": 50,
        }
