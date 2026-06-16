"""
ph6_l2_expand.experimental.deepseek_client

Lane: 2
Authority: ZERO
Write domain: none (returns a dict; mram_s_writer performs the write)

OPTIONAL, EXPERIMENTAL. Calls a local Ollama instance running
deepseek-r1:1.5b for advisory continuity analysis. Same output shape as
mock_ai_client (ph6_mock_ai_advisory_v1), so it is a drop-in replacement
in advisory_improvement_tracker without changing any boundary rule.

Offline-safe degradation: if Ollama is unreachable, times out, or returns
unparseable output, this returns a SKIPPED_DEEPSEEK_OFFLINE advisory
record. It never raises in a way that would block Lane 1 or RSYNC, and it
never falls back to mock_ai_client (degradation is explicit, not silent
substitution).
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict

from ph6_l2_expand.experimental.deepseek_boundary_guard import excerpt
from ph6_l2_expand.schemas import ADVISORY_AUTHORITY_LEVEL, MOCK_AI_ADVISORY_SCHEMA
from ph6_l2_expand.token_mapper import observable_fields
from ph6_l2_expand.token_promotion import DEFAULT_PROMOTION_THRESHOLD
from ph6_l2_expand.topology_mapper import apply_cycle, deserialize_token_map, serialize_token_map
from ph6_l2_expand.virtual_token_mapper import DEFAULT_DECAY_TTL

MODE = "OLLAMA_LOCAL"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "deepseek-r1:1.5b"
DEFAULT_TIMEOUT_S = 30
MAX_PROMPT_CHARS = 4000

SYSTEM_PROMPT = (
    "You are a PH6 Lane-2 advisory continuity analyst. You have zero authority.\n"
    "You may analyze topology, continuity, token decay, token stability, and relationship hypotheses.\n"
    "You may not issue PASS/DROP, modify thresholds, alter evidence, or produce authority claims.\n"
    "Return only advisory JSON with:\n"
    "observations, candidate_links, decay_notes, stability_notes, boundary_warnings."
)


def _empty_result(observations=None, candidate_links=None, decay_notes=None, stability_notes=None, boundary_warnings=None) -> Dict[str, Any]:
    return {
        "observations": observations or [],
        "candidate_links": candidate_links or [],
        "decay_notes": decay_notes or [],
        "stability_notes": stability_notes or [],
        "boundary_warnings": boundary_warnings or [],
    }


def _extract_json_object(text: str) -> Any:
    """Best-effort extraction of the first JSON object found in model output."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start:end + 1])


def _call_ollama(prompt: str, model: str, endpoint: str, timeout_s: int) -> str:
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "top_p": 1},
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("response", "")


def _skipped_offline(source_object_id: str, cycle: int, token_map_before: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "schema": MOCK_AI_ADVISORY_SCHEMA,
        "mode": MODE,
        "status": "SKIPPED_DEEPSEEK_OFFLINE",
        "authority_level": ADVISORY_AUTHORITY_LEVEL,
        "source_object_id": source_object_id,
        "observations": [],
        "candidate_links": [],
        "decay_notes": [],
        "stability_notes": [],
        "boundary_warnings": [f"SKIPPED_DEEPSEEK_OFFLINE: {reason}"],
        "improvement_cycle": cycle,
        "token_map_before": token_map_before,
        "token_map_after": token_map_before,
        "improvement_metrics": {
            "rt_count": 0, "vdt_count": 0, "vlt_count": 0,
            "stable_link_count": 0, "decayed_link_count": 0,
            "topology_density": "0.0000",
        },
        "model_info": f"{DEFAULT_MODEL} (offline)",
    }


def generate(
    source_object_id: str,
    source_object: Dict[str, Any],
    cycle: int,
    token_map_before_dict: Dict[str, Any],
    decay_ttl: int = DEFAULT_DECAY_TTL,
    promotion_threshold: int = DEFAULT_PROMOTION_THRESHOLD,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> Dict[str, Any]:
    fields = observable_fields(source_object)
    prompt = (
        SYSTEM_PROMPT
        + "\n\nSource object fields (read-only, advisory only):\n"
        + json.dumps({"source_object_id": source_object_id, "fields": fields}, sort_keys=True)
    )[:MAX_PROMPT_CHARS]

    try:
        raw_text = _call_ollama(prompt, model, endpoint, timeout_s)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return _skipped_offline(source_object_id, cycle, token_map_before_dict, str(exc))

    try:
        parsed = _extract_json_object(raw_text)
        if not isinstance(parsed, dict):
            raise ValueError("model output JSON is not an object")
        result = _empty_result(
            observations=parsed.get("observations"),
            candidate_links=parsed.get("candidate_links"),
            decay_notes=parsed.get("decay_notes"),
            stability_notes=parsed.get("stability_notes"),
            boundary_warnings=parsed.get("boundary_warnings"),
        )
    except (ValueError, json.JSONDecodeError):
        result = _empty_result(
            observations=["UNPARSEABLE_MODEL_OUTPUT"],
            boundary_warnings=["model output was not valid JSON; candidate_links discarded"],
        )

    # Only well-formed {from,to,relation} links are honored.
    safe_links = [
        link for link in result["candidate_links"]
        if isinstance(link, dict) and {"from", "to", "relation"} <= set(link)
        and all(isinstance(link[k], str) for k in ("from", "to", "relation"))
    ]

    token_map = deserialize_token_map(token_map_before_dict)
    token_map_before = serialize_token_map(token_map)

    token_map, metrics, decay_notes, promoted = apply_cycle(
        token_map, source_object_id, source_object, safe_links, cycle,
        decay_ttl=decay_ttl, promotion_threshold=promotion_threshold,
    )

    return {
        "schema": MOCK_AI_ADVISORY_SCHEMA,
        "mode": MODE,
        "authority_level": ADVISORY_AUTHORITY_LEVEL,
        "source_object_id": source_object_id,
        "observations": [str(o) for o in result["observations"]],
        "candidate_links": safe_links,
        "decay_notes": [str(n) for n in result["decay_notes"]] + decay_notes,
        "stability_notes": [str(n) for n in result["stability_notes"]] + [f"promoted:{tid}" for tid in promoted],
        "boundary_warnings": [str(w) for w in result["boundary_warnings"]],
        "improvement_cycle": cycle,
        "token_map_before": token_map_before,
        "token_map_after": serialize_token_map(token_map),
        "improvement_metrics": metrics,
        "model_info": model,
        "raw_response_excerpt": excerpt(raw_text),
    }
