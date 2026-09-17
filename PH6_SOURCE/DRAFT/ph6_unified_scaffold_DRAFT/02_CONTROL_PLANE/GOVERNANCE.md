# PH6 Governance Closure Rules

## 1. Authority Scope
Within a sealed version scope, the most recent ratified statement governs conflicting prior statements.

## 2. Cross-Version Override
No cross-version override is valid unless accompanied by:
- version increment
- explicit supersession declaration
- justification
- affected section list

## 3. Artifact Binding
Every authoritative artifact must declare:
- `PH6_VERSION`
- `CONST_SET_HASH`
- `GOLDEN_VECTOR_HASH`
- `GOVERNANCE_HASH`
- `RATIFICATION_STATE`

## 4. Required Validation
No artifact may be promoted unless all required checks pass:
- schema validation
- canonical formatting validation
- manifest/hash verification
- deterministic replay validation
- golden vector conformance

Any validation failure:
- CI status = FAIL
- merge is blocked
- artifact cannot be promoted

## 5. Audit Triggers
Audit is mandatory:
- on every pull request
- on every merge to main
- on any change affecting constants, gate logic, normalization, persistence, or hash rules

## 6. Change Classification
- Runtime adjudication changes require version increment.
- Governance or workflow changes must be declared explicitly.
- Silent behavioral drift is forbidden.

## 7. Terminology
Canonical audit log:
**Violations & Resolutions Log** (non-interpretive record)

## 8. Ratification Transition Rules
### PROPOSED → RATIFIED
Requires:
- all validation gates PASS
- audit completed
- explicit approval by maintainer

### RATIFIED → SEALED
Requires:
- version freeze
- manifest + hashes locked
- no further modification allowed

Any modification to a RATIFIED or SEALED artifact requires a new version.

## 9. Replay Equality Definition
Two runs are equal iff:
- PASS/DROP sequence is identical
- ordering is identical
- length is identical

Byte-level equality is required. No tolerance or epsilon is allowed.

## 10. Golden Vector Authority
Golden vectors are authoritative behavioral specification.

If implementation output differs from `Y_gold`:
- implementation is incorrect
- release status is BLOCKED
