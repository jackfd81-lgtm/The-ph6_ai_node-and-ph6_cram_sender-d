#!/usr/bin/env python3
"""
PH6 Research Agent v1.3 - Provider-neutral (OpenAI or Anthropic)
Loads ontology from ph6_ontology.yaml
Searches, scores, and stores candidates.

Lane 2 advisory tool. Emits KEEP/DISCARD ingestion recommendations only.
Has zero governance authority and does not produce PASS/DROP verdicts.
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List

from .hashing import blake2b256_bytes
from .atomic import atomic_write
from .ph6_common import (
    SCORING_AXES,
    ADMISSIBILITY_FIELDS,
    OntologyError,
    compute_ph6_fit,
    resolve_threshold,
    load_ontology_checked,
    validate_scored_result,
    decide_recommendation,
)

# ========== Configuration ==========
KNOWLEDGE_BASE = Path("./ph6_knowledge_base")
DISCARDED_DIR = KNOWLEDGE_BASE / "_discarded"
KEPT_DIR = KNOWLEDGE_BASE / "_kept"

# ========== Provider abstraction ==========
class LLMScorer:
    def __init__(self, provider: str, model: str, api_key: str):
        self.provider = provider.lower()
        self.model = model
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError("Provider must be 'openai' or 'anthropic'")

    def score(self, domain_id: str, candidate: Dict, weights: Dict[str, float]) -> Dict:
        prompt = self._build_prompt(domain_id, candidate)
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content
        else:  # anthropic
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            raise ValueError(f"No JSON found in LLM response: {text[:200]}")
        scores = json.loads(json_match.group())
        validate_scored_result(scores)
        scores["ph6_fit"] = compute_ph6_fit(scores, weights)
        return scores

    def _build_prompt(self, domain_id: str, candidate: Dict) -> str:
        axes_list = ", ".join(SCORING_AXES)
        # Deterministic example derived from the axis set (never drifts).
        # Admissibility booleans are appended so the model always emits them.
        example = {ax: (i % 10) + 1 for i, ax in enumerate(SCORING_AXES)}
        for field in ADMISSIBILITY_FIELDS:
            example[field] = False
        example_json = json.dumps(example, separators=(",", ":"))
        n = len(SCORING_AXES)
        return f"""You are scoring a research candidate for the PH6-CRAM framework.

DOMAIN: {domain_id}
TITLE: {candidate.get('title', '')}
DESCRIPTION: {candidate.get('abstract', candidate.get('description', ''))}

AXES (each 0-10, higher is better):
{axes_list}.

ADMISSIBILITY (report as booleans; these are HARD gates decided in code, not scores):
- requires_cloud_only_authority: true if the candidate CANNOT run locally/at edge
  and depends on cloud-only measurement authority.
- allows_advisory_override_of_measurement: true if advisory/AI output can override
  measurement (Lane-1) authority.
Either being true forces rejection regardless of axis scores. Report them honestly;
do not soften them into low axis scores.

QUALITY DEGRADERS (lower the relevant axis scores; not hard gates):
- Reduces determinism compared to raw measurement
- Cannot preserve raw evidence
- Cannot expose provenance / chain of custody
- Cannot be audited
- Produces black-box outputs without confidence/error bounds
- Breaks reproducibility

Return only one JSON object with the {n} integer axis fields (0-10) plus the two
boolean admissibility fields, no other text. Do NOT include ph6_fit; it is computed
separately.

Example:
{example_json}
"""

# ========== Search stubs (replace with real APIs) ==========
def search_arxiv(query: str, limit: int = 10) -> List[Dict]:
    print(f"  [arxiv] {query}")
    return [{"title": f"Dummy arXiv: {query}", "url": "http://arxiv.org/abs/0000.0000", "abstract": "A dummy paper for demonstration."}]

def search_github(query: str) -> List[Dict]:
    print(f"  [github] {query}")
    return [{"title": f"dummy/{query.replace(' ', '-')}", "url": "https://github.com/dummy", "description": "A dummy repo."}]

def search_ieee(query: str) -> List[Dict]:
    return []
def search_patents(query: str) -> List[Dict]:
    return []
def search_standards(query: str) -> List[Dict]:
    return []
def search_acm(query: str) -> List[Dict]:
    return []
def search_scholar(query: str) -> List[Dict]:
    return []
def search_nist(query: str) -> List[Dict]:
    return []

SOURCE_MAP = {
    "arxiv": search_arxiv,
    "github": search_github,
    "ieee": search_ieee,
    "patents": search_patents,
    "standards": search_standards,
    "acm": search_acm,
    "scholar": search_scholar,
    "nist": search_nist,
}

# ========== Main agent ==========
def run_agent(ontology_path: str, provider: str, model: str, api_key: str):
    ontology = load_ontology_checked(ontology_path)
    scorer = LLMScorer(provider, model, api_key)
    keep_threshold = resolve_threshold(ontology)
    weights = ontology["ph6_weights"]

    KNOWLEDGE_BASE.mkdir(exist_ok=True)
    DISCARDED_DIR.mkdir(exist_ok=True)
    KEPT_DIR.mkdir(exist_ok=True)

    # ontology["domains"] is a mapping (dict) of domain_id -> domain_config
    for domain_id, domain_config in ontology["domains"].items():
        print(f"\n=== Domain: {domain_id} ===")
        domain_min = domain_config.get("min_score", keep_threshold)

        for query in domain_config.get("search_queries", []):
            for source_name in domain_config.get("sources", []):
                search_func = SOURCE_MAP.get(source_name)
                if not search_func:
                    continue
                results = search_func(query)
                for res in results:
                    # Stable canonical hash based on domain, source, title, URL
                    hash_input = f"{domain_id}|{source_name}|{res.get('title')}|{res.get('url')}"
                    unique = blake2b256_bytes(hash_input.encode())[:16]

                    # Check if already scored (kept or discarded)
                    kept_path = KEPT_DIR / f"{domain_id}_{unique}.json"
                    discarded_path = DISCARDED_DIR / f"{domain_id}_{unique}.json"
                    if kept_path.exists() or discarded_path.exists():
                        continue

                    print(f"  Scoring: {res.get('title', '?')[:60]}")
                    try:
                        scores = scorer.score(domain_id, res, weights)
                        ph6_fit = scores.pop("ph6_fit")
                        # Separate admissibility booleans from axis scores.
                        admissibility = {f: scores.pop(f) for f in ADMISSIBILITY_FIELDS}
                        recommendation, reject_reasons = decide_recommendation(
                            ph6_fit, domain_min, admissibility
                        )
                        candidate_record = {
                            "id": unique,
                            "domain": domain_id,
                            "source": source_name,
                            "title": res.get("title"),
                            "url": res.get("url"),
                            "abstract": res.get("abstract") or res.get("description"),
                            "scores": scores,
                            "admissibility": admissibility,
                            "ph6_fit": ph6_fit,
                            "recommendation": recommendation,
                            "reject_reasons": reject_reasons,
                        }
                        if recommendation == "KEEP":
                            out_path = kept_path
                            print(f"    -> KEEP (PH6Fit={ph6_fit:.2f} >= {domain_min})")
                        else:
                            out_path = discarded_path
                            reason_str = ",".join(reject_reasons)
                            print(f"    -> DISCARD (PH6Fit={ph6_fit:.2f}; {reason_str})")
                        payload = json.dumps(candidate_record, indent=2).encode()
                        atomic_write(out_path, payload)
                    except Exception as e:
                        print(f"    -> ERROR: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", default="ph6_ontology.yaml")
    parser.add_argument("--provider", choices=["openai", "anthropic"], default="anthropic")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--api-key", help="Set PH6_API_KEY or pass here")
    args = parser.parse_args()
    api_key = args.api_key or os.environ.get("PH6_API_KEY")
    if not api_key:
        raise ValueError("API key required. Set PH6_API_KEY environment variable or pass --api-key")
    run_agent(args.ontology, args.provider, args.model, api_key)
