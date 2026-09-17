# ph6_l2_expand.lmpq_proposed — PROPOSED, NOT RATIFIED

Lane: 2. Authority: ZERO. Write domain: MRAM-S only (via
`ph6_l2_expand.mram_s_writer`, no direct filesystem I/O in this package).

This package implements the design in
`PH6_SOURCE/DRAFT/PH6-LMPQ-001-PROPOSED-SPEC-v0.1.md`:

- `tokens.py` — `RLT` (Reference Loss Token), `PLT` (Provenance Link
  Token), `AHT` (Archival Hydration Token). None of these are members of
  `ph6_l2_expand.schemas.TOKEN_TYPES`. That set stays locked to
  `{RT, VDT, VLT}`.
- `life_cram_bcv2.py` — "Bounded Campaign Vector v2" bundle schema
  (`ph6.lmpq.life_cram_bcv2.v1`) for packaging one Life-CRAM experience.
- `soso_jedi_adapter.py` — deterministic single-token provenance lookup
  against the existing, unmodified
  `PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py::BookVCoreEngine`.
- `chain_runner.py` — end-to-end demonstration of the full proposed
  LMPQ-001 path through a temp MRAM-S directory.
- `bench_four_experiences.py` — the four-experience bench (PM-02).

## What this package must never do

- Add anything to `ALLOWED_TOKEN_TYPES` / `TOKEN_TYPES`.
- Import `ph6.cram_pu` (Lane-1 runtime).
- Write to `/var/ph6/cram-0`, `cram-a`, or `cram-r` (or any path
  containing those segments — `mram_s_writer` already refuses this).
- Emit `PASS`, `DROP`, or any forbidden-vocabulary field
  (`ph6_l2_expand.boundary_guard` already quarantines this).
- Modify `PH6_SOURCE/AI/soso_jedi/jedi/swarm_sim_bp.py`.

## Status

PROPOSED. `ratified_by: null`. Promotion of RLT/PLT/AHT into the
authoritative token set is a separate future decision, not made here.
