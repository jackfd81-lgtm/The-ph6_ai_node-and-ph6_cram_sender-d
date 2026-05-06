# CRAM-PU-LIVE-1.0 Fresh-Checkout Verification

**Date:** 2026-05-06  
**Commit:** 95327f1  
**Repository:** The-ph6_ai_node-and-ph6_cram_sender-d  
**Branch:** main  

## Procedure

1. Local clone from `/home/jack` (no-hardlinks, fresh tree)
2. `git status --short` — confirmed clean
3. `bash ph6/cram_pu/run_cram_pu_live_1_0.sh --packets 12`
4. `python3 ph6/cram_pu/tools/cram_pu_fi_suite.py`
5. Inspected `manifest.json` and `.blake2b` sidecars in generated runtime dir
6. Confirmed only `ph6/cram_pu/runtime/` untracked after run (evidence files only)
7. Clone removed

## Results

| Check | Result |
|---|---|
| Clean path `CRAM_PU_LIVE_1_0_PASS` | True |
| Schema validation | PASS |
| FI suite `8/8 CRAM_PU_FI_SUITE_PASS` | True |
| `manifest.json` written | Yes |
| `.blake2b` sidecars present (9 PASS commits) | Yes |
| Source drift after run | NONE |
| Edited-tree dependency | NONE |

## Conclusion

Commit `95327f1` is reproducible from source. The runtime produces correct evidence
files and defends all eight failure-injection faults from a clean checkout.
No source modifications required.
