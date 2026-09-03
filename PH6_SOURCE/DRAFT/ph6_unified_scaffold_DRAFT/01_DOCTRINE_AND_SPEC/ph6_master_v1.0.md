# PH6 Master Specification v1.0

- PH6_VERSION: v1.0
- RATIFICATION_STATE: PROPOSED
- GOVERNANCE_HASH: d6259f1abc55a8b356c41cb5aaa06a2a40426736331f47a7844611f9381d8519
- CONST_SET_HASH: 2cb94b3d1a81470000bfb8fb29ea97cea322a84f687bb3ac36f29cc3395857d2
- GOLDEN_VECTOR_HASH: 22328625423cdaaf7dc4b3ff63bd54eb0bbd26ad1ad3ac2b3aa0db9211871578

## Purpose
PH6 is a deterministic signal-gating measurement instrument. Output is restricted to `PASS` or `DROP`.

## Lane 1 Rules
1. First frame drops because no predecessor exists for motion computation.
2. Laplacian variance below `LAP_VAR_MIN` drops immediately.
3. Entropy below `ENTROPY_DROP_THRESH` is counted across consecutive frames. Drop occurs when consecutive count reaches `ENTROPY_PERSISTENCE`.
4. Motion fraction below `MOTION_STASIS_MAX` is counted across consecutive frames. Drop occurs when consecutive count reaches `MOTION_WINDOW`.
5. Structural anomaly veto:
   - resolution area and byte size use rolling z-score windows
   - z-score activates only after `ZSCORE_MIN_WINDOW` historical frames
   - if either absolute z-score exceeds its threshold, verdict is `DROP`
