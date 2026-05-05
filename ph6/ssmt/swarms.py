from .swarm_base import BaseSwarm
from .models import SwarmInput
from .drift_math import drift_from_decay, confidence_from_drift, clamp_fp
from .temporal_decay import exponential_decay_fp


def _tok_by_type(tok_refs: list, tok_type: str) -> list:
    return [r for r in tok_refs if f"/{tok_type}/" in r or f":{tok_type}:" in r
            or r.startswith(f"tok://{tok_type}/")]


class S1ActiveMemorySwarm(BaseSwarm):
    swarm_id = "S1"
    role = "active_memory"
    ttl_seconds = 30

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "active_cram_refs": list(data.cram_refs),
            "active_tok_refs": list(data.tok_refs),
            "summary": "current advisory state snapshot",
            "_confidence_fp": 9500,
        }


class S2ContextAnchorSwarm(BaseSwarm):
    swarm_id = "S2"
    role = "context_anchor"
    ttl_seconds = 120

    def compute_payload(self, data: SwarmInput) -> dict:
        vdt_refs = _tok_by_type(data.tok_refs, "VDT")
        # Each VDT token applies 1000fp of decay pressure (max 5000fp)
        decay_pressure = clamp_fp(len(vdt_refs) * 1000, hi=5000)
        confidence = confidence_from_drift(8000, decay_pressure)
        return {
            "context_hint": "what this system roughly is",
            "cram_count": len(data.cram_refs),
            "tok_count": len(data.tok_refs),
            "vdt_decay_pressure_fp": decay_pressure,
            "_confidence_fp": confidence,
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
            "_confidence_fp": 8500,
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
            "_confidence_fp": 10000,
        }


class S5HistoricalAwarenessSwarm(BaseSwarm):
    swarm_id = "S5"
    role = "historical_awareness"
    ttl_seconds = 1800

    def compute_payload(self, data: SwarmInput) -> dict:
        vlt_refs = _tok_by_type(data.tok_refs, "VLT")
        vdt_refs = _tok_by_type(data.tok_refs, "VDT")
        # VLT adds long-term stability confidence (max +3000fp)
        stability_bonus = clamp_fp(len(vlt_refs) * 500, hi=3000)
        # VDT applies decay pressure (max 4000fp)
        decay_penalty = clamp_fp(len(vdt_refs) * 800, hi=4000)
        confidence = clamp_fp(confidence_from_drift(7000 + stability_bonus, decay_penalty))
        return {
            "stabilized_patterns": [],
            "long_term_cram_refs": list(data.cram_refs),
            "vlt_stability_fp": stability_bonus,
            "vdt_decay_fp": decay_penalty,
            "_confidence_fp": confidence,
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
            "_confidence_fp": 4000,
        }


class S7UpdateIntakeSwarm(BaseSwarm):
    swarm_id = "S7"
    role = "update_intake"
    ttl_seconds = 60

    def compute_payload(self, data: SwarmInput) -> dict:
        return {
            "new_advisory_refs": list(data.advisory_refs),
            "watching": True,
            "_confidence_fp": 9000,
        }


class S8DriftTrackingSwarm(BaseSwarm):
    swarm_id = "S8"
    role = "drift_tracking"
    ttl_seconds = 300

    def compute_payload(self, data: SwarmInput) -> dict:
        vdt_refs = _tok_by_type(data.tok_refs, "VDT")
        # Each VDT implies ~60s of accumulated decay history
        age_proxy_seconds = len(vdt_refs) * 60
        decay_fp = exponential_decay_fp(age_proxy_seconds, half_life_seconds=300)
        # Gap pressure: fewer CRAM refs = more uncertainty
        gap_fp = clamp_fp(max(0, (5 - len(data.cram_refs)) * 2000))
        drift = drift_from_decay(decay_fp, gap_fp=gap_fp)
        confidence = confidence_from_drift(7500, drift)
        return {
            "drift_detected": drift > 2000,
            "vdt_count": len(vdt_refs),
            "age_proxy_seconds": age_proxy_seconds,
            "decay_fp": decay_fp,
            "gap_fp": gap_fp,
            "conflict_signals": [],
            "_drift_score": drift,
            "_confidence_fp": confidence,
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
            "_confidence_fp": 5000,
        }
