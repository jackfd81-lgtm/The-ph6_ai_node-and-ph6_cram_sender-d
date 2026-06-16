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
