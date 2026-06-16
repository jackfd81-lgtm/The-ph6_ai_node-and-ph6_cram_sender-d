# PH6 Research Agent

Lane-2 advisory research-intake tooling. Searches external sources, scores
candidates against an 11-axis ontology, and writes KEEP/DISCARD candidate
records to a local knowledge base.

## Authority

- Non-authoritative. Lane-2 / advisory only.
- Does not produce CRAM PASS/DROP verdicts and is not Lane-1 measurement
  authority.
- Classifies research candidates only as `KEEP` / `DISCARD` within this
  package's own knowledge base namespace.

## Hard gates (code-enforced, not prompt-only)

`ph6_common.decide_recommendation()` runs a binary admissibility gate before
any threshold comparison:

- `requires_cloud_only_authority == True` -> `DISCARD`
  (reason `REQUIRES_CLOUD_ONLY_AUTHORITY`)
- `allows_advisory_override_of_measurement == True` -> `DISCARD`
  (reason `ALLOWS_ADVISORY_OVERRIDE_OF_MEASUREMENT`)

Only candidates that clear both gates are compared against `keep_threshold`
(or a domain's `min_score`). `validate_scored_result()` requires both fields
to be present and to be real booleans, so a missing or malformed model
response is a parse error, not a silently-absent gate.

## Layout

```
ph6/research_agent/
  ph6_common.py   - scoring axes, gate logic, ontology validation
  ph6_agent.py    - search + score + KEEP/DISCARD pipeline
  hashing.py      - blake2b256_bytes (BLAKE2b-256, digest_size=32)
  atomic.py       - atomic_write (write-tmp/fsync/replace/fsync-dir)
  ph6_ontology.yaml - scaffold ontology (replace before production use)
  tests/          - contract tests
```

## Status

`ph6_ontology.yaml` is a scaffold (dummy domain, dummy search sources) for
smoke-testing only. Replace with a production ontology before connecting
real search providers.
