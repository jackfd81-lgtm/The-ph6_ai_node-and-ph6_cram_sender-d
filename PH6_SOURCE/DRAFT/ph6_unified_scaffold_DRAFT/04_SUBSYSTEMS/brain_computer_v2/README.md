# Brain Computer v2

Brain Computer v2 is a Python-first external memory and continuity layer built around nodes, edges, notes, and an append-only ledger. The current package preserves the validated implementation as the source of truth and packages it for a ready-to-code developer environment.

## Operational doctrine

- The ledger is append-only; every meaningful state change must be recorded for traceability.
- Supersession preserves history; old nodes are deactivated and linked forward with `DELTA_OF`.
- Retrieval favors active nodes while preserving contradiction-aware context.
- Verified state exports and canonical hashes are the recovery anchor.
- Perplexity API integration is advisory and external; Brain Computer v2 remains the organizing memory substrate.

## Package contents

- `src/brain_computer_v2/brain_computer_v2.py`: core implementation.
- `src/brain_computer_v2/perplexity_adapter.py`: simple Perplexity API adapter.
- `src/brain_computer_v2/neo4j_export.py`: helper wrapper for Neo4j CSV export.
- `tests/`: harness and adapter tests.
- `state/`: current verified state, final hash, and Neo4j CSV exports.
- `scripts/neo4j_admin_import_template.sh`: bulk import template.
- `typescript_interfaces.ts`: companion TypeScript interfaces for downstream integration.

## Maintenance schedule

### Daily
- Run research ingests if needed.
- Call the session hash sync checkpoint after multi-turn research.
- Export a verified state artifact and back it up.

### Weekly
- Run the full test harness.
- Rebuild Neo4j CSV exports.
- Review inactive/superseded nodes for structural hygiene.

### Monthly
- Review retrieval tag vocabulary.
- Validate backup restore from a verified export.
- Review adapter/API assumptions against current Perplexity docs.

## Quick start

```bash
python -m unittest discover -s tests
```

```python
from brain_computer_v2 import BrainComputerV2, PerplexityAdapter

brain = BrainComputerV2(state='state/brain_computer_v2_kernel_ingest_state_final.json')
adapter = PerplexityAdapter(brain)
```

## Neo4j export/import

Use the packaged state CSVs or regenerate them from the Python module. For large imports, use `neo4j-admin database import full` with the provided shell template against an empty or offline database.
