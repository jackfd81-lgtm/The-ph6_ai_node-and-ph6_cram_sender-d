PH6 / CRAM — L2_EXPAND ROOT PACKAGE PLACEMENT RATIFICATION

Decision:
Ratify /home/jack/ph6_l2_expand/ as a controlled repo-root package placement exception.

Scope:
This ratification applies only to the Lane-2 SoSo / token / mock-AI / DeepSeek advisory subsystem known as ph6_l2_expand.

Reason:
The package must remain top-level to support direct module execution and imports:
python3 -m ph6_l2_expand.cli
from ph6_l2_expand.xxx import ...

Authority:
Authority ZERO.
Lane 2 only.
MRAM-S only.
Book V experimental/advisory only.

Allowed:
- Advisory token mapping
- RT / VDT / VLT generation
- Mock offline AI tests
- DeepSeek local/offline advisory tests
- MRAM-S writes
- Read-only references to Lane-1 evidence identifiers
- Read-only Lane-1 regression testing

Forbidden:
- CRAM-0 writes
- CRAM-A writes
- CRAM-R writes
- PSEUDO-M modification
- PSEUDO-A modification
- EvidencePacket mutation
- Replay dependency
- Threshold mutation
- PASS/DROP generation
- Any Lane-2 to Lane-1 authority return path

Correction to implementation report:
Replace "No Lane-1 file was read or modified" with:
"No Lane-1 file was modified. Lane-1 code may have been read/imported only for regression testing, with no authority mutation or advisory write path."

Status:
Ratified as experimental Lane-2 package placement only.
Not ratified as Lane-1 authority.
Not production authority.
Not part of CRAM/PSEUDO runtime authority.

Ratified by:
Jack / Lane 1 Operator
Date:
2026-06-14

{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-14T13:10:00Z","api_call_log_ref":"session-e320f74c-cont","ratified_by":"jack"}

## Operational MRAM-S Path Map (ratified 2026-06-16)

Canonical active MRAM-S root on jackjack Pi 5:

```text
/var/ph6/mram-s/swarms/    — SSMT swarm packets and replay receipts
/var/ph6/mram-s/tokens/    — tok lifecycle records
/var/ph6/mram-s/advisory/  — ph6_l2_expand advisory output
/var/ph6/mram-s/reports/   — reports
```

ph6_l2_expand CLI invocations must use:

```text
--out /var/ph6/mram-s/advisory/
```

Preserved local sentinel records:

```text
/home/jack/ph6/mram-s/zero2w/
```

SEALED legacy SoSo Lite corpus — DO NOT MIX:

```text
/home/jack/ph6lite_cam/mram_s/
schema: ph6.soso_lite.v0.1
records: 16,147
status: SEALED_LEGACY_CORPUS
```

No new ph6_l2_expand records may be written into the sealed legacy corpus.

{"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-06-16T10:55:00Z","api_call_log_ref":"session-20260616-mram-path-ratification","ratified_by":"jack"}
