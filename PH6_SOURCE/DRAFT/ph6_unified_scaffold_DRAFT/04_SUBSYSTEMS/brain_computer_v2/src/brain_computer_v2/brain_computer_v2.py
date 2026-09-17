import json
import uuid
import hashlib
from copy import deepcopy
from datetime import datetime, timezone

ALLOWED_CLASSIFICATIONS = {
    "ROLE", "GOAL", "CONSTRAINT", "RISK", "CONTEXT",
    "OUTPUT", "NEXT_STEP", "LESSON", "OBSERVATION"
}

ALLOWED_RELATIONS = {
    "RELATES_TO", "PRECEDES", "DELTA_OF", "DERIVED_FROM",
    "CONTRADICTS", "SUPPORTS", "REFERENCES"
}

NOTE_TYPES = {
    "ambiguities", "continuity_observations", "contradictions"
}


class BrainComputerV2:
    """Organizational-only external memory and continuity layer. Supports verified state export and Neo4j CSV bulk import."""

    def __init__(self, brain_id="BRAIN-BLANK-001", state=None):
        self.brain_id = brain_id
        self.nodes = []
        self.edges = []
        self.ledger = []
        self.notes = {
            "ambiguities": [],
            "continuity_observations": [],
            "contradictions": []
        }
        self._sequence = 0
        if state is not None:
            self.importState(state)

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _next_sequence(self):
        self._sequence += 1
        return self._sequence

    def _sync_sequence(self):
        values = [0]
        values.extend(n.get("sequence", 0) for n in self.nodes)
        values.extend(e.get("sequence", 0) for e in self.ledger)
        self._sequence = max(values)

    def _find_node(self, node_id):
        return next((n for n in self.nodes if n["id"] == node_id), None)

    def _require_node(self, node_id):
        node = self._find_node(node_id)
        if not node:
            raise ValueError(f"Node not found: {node_id}")
        return node

    def _validate_classification(self, classification):
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"Invalid classification: {classification}")

    def _validate_relation(self, relation):
        if relation not in ALLOWED_RELATIONS:
            raise ValueError(f"Invalid relation: {relation}")

    def _ensure_unique_node_id(self, node_id):
        if self._find_node(node_id):
            raise ValueError(f"Duplicate node id: {node_id}")

    def appendLedgerEvent(self, event, target, reason):
        entry = {
            "event": event,
            "target": target,
            "reason": reason,
            "created_at": self._now(),
            "sequence": self._next_sequence()
        }
        self.ledger.append(entry)
        return deepcopy(entry)

    def addNode(self, node_type, label, classification, content, active=True, retrieval_tags=None, node_id=None):
        self._validate_classification(classification)
        node_id = node_id or f"{classification}-{uuid.uuid4().hex[:8].upper()}"
        self._ensure_unique_node_id(node_id)
        node = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "classification": classification,
            "content": content,
            "sequence": self._next_sequence(),
            "created_at": self._now(),
            "active": bool(active),
            "retrieval_tags": list(retrieval_tags or [])
        }
        self.nodes.append(node)
        self.appendLedgerEvent("NODE_ADDED", node_id, f"Added {classification} node: {label}")
        return deepcopy(node)

    def addEdge(self, from_id, to_id, relation):
        self._validate_relation(relation)
        self._require_node(from_id)
        self._require_node(to_id)
        edge = {"from": from_id, "to": to_id, "relation": relation}
        self.edges.append(edge)
        self.appendLedgerEvent("EDGE_ADDED", f"{from_id}->{to_id}", f"Relation: {relation}")
        return deepcopy(edge)

    def addNote(self, note_type, text):
        if note_type not in NOTE_TYPES:
            raise ValueError(f"Invalid note type: {note_type}")
        self.notes[note_type].append(text)
        self.appendLedgerEvent("NOTE_ADDED", note_type, text)
        return text

    def supersedeNode(self, old_node_id, node_type, label, classification, content, retrieval_tags=None):
        old_node = self._require_node(old_node_id)
        if not old_node.get("active"):
            raise ValueError(f"Node already inactive: {old_node_id}")
        old_node["active"] = False
        self.appendLedgerEvent("NODE_DEACTIVATED", old_node_id, "Superseded by new node")
        new_node = self.addNode(
            node_type=node_type,
            label=label,
            classification=classification,
            content=content,
            active=True,
            retrieval_tags=retrieval_tags or old_node.get("retrieval_tags", [])
        )
        self.addEdge(new_node["id"], old_node_id, "DELTA_OF")
        self.appendLedgerEvent("NODE_SUPERSEDED", new_node["id"], f"Supersedes {old_node_id}")
        return deepcopy(new_node)

    def retrieveContext(self):
        node_by_id = {n["id"]: n for n in self.nodes}
        result = {}

        def add_result(node):
            if node:
                result[node["id"]] = node

        def latest_active(classification):
            matches = [
                n for n in self.nodes
                if n.get("active") and n.get("classification") == classification
            ]
            matches.sort(key=lambda n: (n.get("sequence", 0), n.get("id", "")), reverse=True)
            return matches[0] if matches else None

        for node in self.nodes:
            if node.get("active") and node.get("classification") in {"ROLE", "CONSTRAINT"}:
                add_result(node)

        add_result(latest_active("GOAL"))
        add_result(latest_active("NEXT_STEP"))

        anchor_ids = set(result.keys())
        allowed_relations = {"RELATES_TO", "SUPPORTS", "DERIVED_FROM", "CONTRADICTS"}

        for edge in self.edges:
            if edge.get("relation") not in allowed_relations:
                continue
            candidates = []
            if edge.get("from") in anchor_ids:
                candidates.append(edge.get("to"))
            if edge.get("to") in anchor_ids:
                candidates.append(edge.get("from"))
            for candidate_id in candidates:
                candidate = node_by_id.get(candidate_id)
                if not candidate:
                    continue
                if not candidate.get("active"):
                    continue
                if candidate.get("classification") not in {"CONTEXT", "OUTPUT"}:
                    continue
                add_result(candidate)

        return deepcopy(sorted(result.values(), key=lambda n: (n.get("sequence", 0), n.get("id", ""))))

    def _canonical_state_projection(self, state=None):
        base = deepcopy(state if state is not None else self.exportState())
        if isinstance(base, dict) and "verification" in base:
            base.pop("verification", None)
        return base

    def canonical_state_json(self, state=None):
        projection = self._canonical_state_projection(state)
        return json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def canonical_state_hash(self, state=None):
        canonical_json = self.canonical_state_json(state)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def state_verification_envelope(self, state=None, session_id=None):
        source = self._canonical_state_projection(state)
        copied = deepcopy(source)
        same_nested_identity = False
        if source.get("nodes") and copied.get("nodes"):
            same_nested_identity = copied["nodes"][0] is source["nodes"][0]
        return {
            "state": source,
            "verification": {
                "schema_version": "bcv2.verify.1",
                "exported_at": self._now(),
                "session_id": session_id or self.brain_id,
                "canonicalization": {
                    "format": "json",
                    "sort_keys": True,
                    "separators": [",", ":"],
                    "encoding": "utf-8",
                    "trailing_newline": False
                },
                "counts": {
                    "nodes": len(source.get("nodes", [])),
                    "edges": len(source.get("edges", [])),
                    "ledger": len(source.get("ledger", [])),
                    "ambiguities": len(source.get("notes", {}).get("ambiguities", [])),
                    "continuity_observations": len(source.get("notes", {}).get("continuity_observations", [])),
                    "contradictions": len(source.get("notes", {}).get("contradictions", []))
                },
                "projection_hash_sha256": self.canonical_state_hash(source),
                "deep_copy_check": {
                    "performed": True,
                    "equal_by_value": copied == source,
                    "same_object_identity": copied is source,
                    "same_nested_identity_detected": same_nested_identity
                }
            }
        }

    def verify_imported_state(self, imported_state):
        if isinstance(imported_state, str):
            with open(imported_state, "r", encoding="utf-8") as f:
                imported_state = json.load(f)
        envelope = imported_state if "verification" in imported_state and "state" in imported_state else self.state_verification_envelope(imported_state)
        state = envelope["state"]
        recorded_hash = envelope["verification"]["projection_hash_sha256"]
        recomputed_hash = self.canonical_state_hash(state)
        reloaded = BrainComputerV2(state=deepcopy(state))
        round_trip_equal = reloaded.exportState() == state
        return {
            "recorded_hash": recorded_hash,
            "recomputed_hash": recomputed_hash,
            "hash_matches": recorded_hash == recomputed_hash,
            "round_trip_equal": round_trip_equal,
            "deep_copy_non_identity": deepcopy(state) is not state
        }

    def export_verified_state(self, path, session_id=None):
        envelope = self.state_verification_envelope(session_id=session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
        self.appendLedgerEvent("STATE_VERIFIED_EXPORTED", path, "Exported state with canonical hash verification envelope")
        return deepcopy(envelope)


    def export_neo4j(self, nodes_path, relationships_path):
        import csv
        nodes = sorted(self.nodes, key=lambda n: (n.get("sequence", 0), n.get("id", "")))
        edges = sorted(self.edges, key=lambda e: (e.get("from", ""), e.get("to", ""), e.get("relation", "")))
        with open(nodes_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([":ID", "id", "type", "label", "classification", "content", "sequence:long", "created_at", "active:boolean", "retrieval_tags", ":LABEL"])
            for n in nodes:
                labels = [n.get("classification", "")]
                w.writerow([
                    n["id"],
                    n["id"],
                    n.get("type", ""),
                    n.get("label", ""),
                    n.get("classification", ""),
                    n.get("content", ""),
                    n.get("sequence", 0),
                    n.get("created_at", ""),
                    str(bool(n.get("active", True))).lower(),
                    json.dumps(n.get("retrieval_tags", []), ensure_ascii=False),
                    ";".join(labels)
                ])
        with open(relationships_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([":START_ID", ":END_ID", ":TYPE"])
            for e in edges:
                w.writerow([e.get("from", ""), e.get("to", ""), e.get("relation", "")])
        return {"nodes": nodes_path, "relationships": relationships_path}


    def commit_session_hash(self, session_id=None, note=None, export_verified_path=None):
        envelope = self.state_verification_envelope(session_id=session_id)
        digest = envelope["verification"]["projection_hash_sha256"]
        payload = {
            "session_id": session_id or self.brain_id,
            "hash": digest,
            "counts": envelope["verification"]["counts"],
            "note": note or "Session hash checkpoint committed"
        }
        self.appendLedgerEvent(
            "SESSION_HASH_COMMITTED",
            payload["session_id"],
            json.dumps(payload, ensure_ascii=False)
        )
        if export_verified_path:
            self.export_verified_state(export_verified_path, session_id=session_id)
        return deepcopy(payload)

    def sync_after_research_session(self, session_id, export_verified_path=None, note=None):
        return self.commit_session_hash(
            session_id=session_id,
            note=note or "Post-research session state sync",
            export_verified_path=export_verified_path
        )

    def exportState(self):
        return deepcopy({
            "brain_id": self.brain_id,
            "nodes": self.nodes,
            "edges": self.edges,
            "ledger": self.ledger,
            "notes": self.notes
        })

    def exportStateToFile(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.exportState(), f, indent=2, ensure_ascii=False)
        self.appendLedgerEvent("STATE_EXPORTED", path, "Exported state to JSON file")
        return path

    def importState(self, state):
        if isinstance(state, str):
            with open(state, "r", encoding="utf-8") as f:
                state = json.load(f)
        if "verification" in state and "state" in state:
            state = state["state"]
        self.brain_id = state.get("brain_id", self.brain_id)
        self.nodes = deepcopy(state.get("nodes", []))
        self.edges = deepcopy(state.get("edges", []))
        self.ledger = deepcopy(state.get("ledger", []))
        self.notes = deepcopy(state.get("notes", {
            "ambiguities": [],
            "continuity_observations": [],
            "contradictions": []
        }))
        self._sync_sequence()
        return self.exportState()


    def loadFromFile(self, path):
        return self.importState(path)

    def searchByTag(self, query, exact=False, node_types=None):
        query_norm = str(query).strip().lower()
        allowed = set(node_types) if node_types else None
        matches = []
        for node in self.nodes:
            if allowed and node.get("classification") not in allowed and node.get("type") not in allowed:
                continue
            tags = [str(tag) for tag in node.get("retrieval_tags", [])]
            tags_norm = [tag.lower() for tag in tags]
            hit = query_norm in tags_norm if exact else any(query_norm in tag for tag in tags_norm)
            if hit:
                matches.append(deepcopy(node))
        matches.sort(key=lambda n: (n.get("sequence", 0), n.get("id", "")))
        return matches

    def allTags(self):
        tag_map = {}
        for node in self.nodes:
            for tag in node.get("retrieval_tags", []):
                key = str(tag)
                tag_map.setdefault(key, []).append(node["id"])
        for key in tag_map:
            tag_map[key].sort()
        return tag_map

    def export_state(self):
        return self.exportState()

    def import_state(self, state):
        return self.importState(state)

    def status(self):
        active_nodes = sum(1 for n in self.nodes if n.get("active"))
        return {
            "brain_id": self.brain_id,
            "nodes": len(self.nodes),
            "active_nodes": active_nodes,
            "edges": len(self.edges),
            "ledger_events": len(self.ledger),
            "sequence": self._sequence
        }
