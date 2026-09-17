import json
import os
from copy import deepcopy
from datetime import datetime, timezone

import requests

from .brain_computer_v2 import BrainComputerV2


class PerplexityAdapter:
    """Simple advisory adapter from Perplexity API into Brain Computer v2."""

    def __init__(self, brain: BrainComputerV2, api_key=None, model="sonar", base_url="https://api.perplexity.ai"):
        self.brain = brain
        self.api_key = api_key or os.getenv("PPLX_API_KEY")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/chat/completions"

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _headers(self):
        if not self.api_key:
            raise ValueError("Missing Perplexity API key. Set PPLX_API_KEY or pass api_key.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat_completion(self, prompt, system_prompt="Be precise and concise.", model=None, temperature=0.2):
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        response = requests.post(self.chat_url, headers=self._headers(), json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def ingest_chat_response(self, prompt, response, goal_node_id=None, retrieval_tags=None):
        response_copy = deepcopy(response)
        content = ""
        citations = []
        model_name = response_copy.get("model", self.model)

        choices = response_copy.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "") or ""
            citations = message.get("citations", []) or response_copy.get("citations", []) or []

        output_node = self.brain.addNode(
            node_type="API_OUTPUT",
            label=f"Perplexity response: {prompt[:60]}",
            classification="OUTPUT",
            content=content,
            retrieval_tags=list(retrieval_tags or []) + ["perplexity", "api", "response", model_name]
        )

        metadata_node = self.brain.addNode(
            node_type="API_CONTEXT",
            label=f"Perplexity request metadata: {prompt[:60]}",
            classification="CONTEXT",
            content=json.dumps({
                "origin": "perplexity",
                "endpoint": self.chat_url,
                "model": model_name,
                "prompt": prompt,
                "ingested_at": self._now(),
                "raw_response": response_copy
            }, ensure_ascii=False),
            retrieval_tags=["perplexity", "metadata", "api"]
        )
        self.brain.addEdge(output_node["id"], metadata_node["id"], "REFERENCES")

        if goal_node_id:
            self.brain.addEdge(goal_node_id, output_node["id"], "SUPPORTS")

        for idx, citation in enumerate(citations, start=1):
            cite_url = citation if isinstance(citation, str) else str(citation)
            cite_node = self.brain.addNode(
                node_type="SOURCE_REF",
                label=f"Perplexity citation {idx}",
                classification="CONTEXT",
                content=cite_url,
                retrieval_tags=["perplexity", "citation", "source"]
            )
            self.brain.addEdge(output_node["id"], cite_node["id"], "REFERENCES")

        self.brain.appendLedgerEvent(
            "PERPLEXITY_RESPONSE_INGESTED",
            output_node["id"],
            f"Ingested Perplexity API response for prompt: {prompt[:80]}"
        )
        return {
            "output_node_id": output_node["id"],
            "metadata_node_id": metadata_node["id"],
            "citation_count": len(citations)
        }

    def research(self, prompt, system_prompt="Be precise and concise.", goal_node_id=None, retrieval_tags=None):
        response = self.chat_completion(prompt=prompt, system_prompt=system_prompt)
        ingest_result = self.ingest_chat_response(
            prompt=prompt,
            response=response,
            goal_node_id=goal_node_id,
            retrieval_tags=retrieval_tags
        )
        return {
            "response": response,
            "ingest_result": ingest_result
        }
