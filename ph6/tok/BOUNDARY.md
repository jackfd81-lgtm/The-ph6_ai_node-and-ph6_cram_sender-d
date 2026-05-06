# TOK-1.0 Boundary Contract

TOK-1.0 is a Lane-2 advisory token lifecycle subsystem.

## Authority

TOK has Authority ZERO.

TOK may never:
- issue PASS
- issue DROP
- alter PASS/DROP
- alter PSEUDO
- alter CRAM
- mutate EvidencePacket
- write authority audit
- block RSYNC
- become replay dependency

## Write Domain

TOK may write only to:

```text
/var/ph6/mram-s/tokens/
```

Allowed files:
- live_tokens.json
- tok_advisory_audit.jsonl
- archive/*.json
- receipts/*.json
- reports/*.json

Forbidden paths:
- /var/ph6/cram-0/
- /var/ph6/cram-a/
- /var/ph6/cram-r/
- /var/ph6/export/
- /var/ph6/audit/
- PSEUDO config paths
- threshold config paths

## Replay Rule

TOK may rebuild advisory topology.

TOK rebuild success does not certify PH6 evidence.

TOK is never required for Lane-1 replay.
