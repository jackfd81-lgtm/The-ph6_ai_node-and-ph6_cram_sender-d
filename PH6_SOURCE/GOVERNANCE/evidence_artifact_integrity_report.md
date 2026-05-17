# PH6 Evidence Artifact Integrity Report
Generated: 2026-05-17T07:30:00Z | Post-C13 Whole-System Audit

## Overall Result: PASS

21,966 artifact files indexed across 22 validation run directories.

## Campaign Artifact Status

| Campaign | Run Stamp | Manifest | Result Hash | Artifact Hash | Final Report | Failure Reg | Receipts | Status |
|---|---|---|---|---|---|---|---|---|
| C08 | 050752Z | older schema | per-segment | ✓ | older schema | older schema | embedded | PASS_OLDER_SCHEMA |
| C09 | 055650Z | ✓ | ✓ | ✓ | ✓ | ✓ | 9 | COMPLETE |
| C10 | 061511Z | ✓ | ✓ | ✓ | ✓ | ✓ | 7 | COMPLETE |
| C11 | 061511Z | ✓ | ✓ | ✓ | ✓ | ✓ | 7 | COMPLETE |
| C12 | 061511Z | ✓ | ✓ | ✓ | ✓ | ✓ | 7 | COMPLETE |
| C13 | 065826Z | ✓ | ✓ | ✓ | ✓ | ✓ | 11 | COMPLETE |

**Note on C08:** Uses older runner schema (`campaign_result_summary.json` instead of `campaign_manifest.json`). All critical evidence fields (result_set_hash, replay_verdict, rsync_blocked, lane2_isolation) are present in the summary. Schema evolution occurred after C08. This is historical, not a failure.

## Preserved Partial Evidence (Per Doctrine)

| Run Stamp | Campaign | Frames | Commit |
|---|---|---|---|
| 063357Z | C13 | 741 | db574d96d |
| 063840Z | C13 | 924 | db574d96d |
| 064235Z | C13 | 14000 (A-D) | faffdb5b5 |

All three committed and preserved. Do not delete.

## .tmp Files

Two files found in `frame_filter/logs/`:
- `frame_filter/logs/live_run.tmp`
- `frame_filter/logs/run_20260429_215052/hot/run_log.tmp`

Not deleted pending human confirmation. Likely frame_filter runtime hot-logs from April 2026 session. Not PH6 evidence.
