# Session Closeout Template

```text
Document ID: PH6-SESSION-CLOSEOUT-TEMPLATE-1.0
Status:      ACTIVE
Purpose:     End-of-session compression packet — fill in and commit
```

---

## Template

```text
SESSION SUMMARY:
  Date:           YYYY-MM-DD
  Campaign:
  Operator:

OPEN ITEMS:
  [List any newly discovered open items or blockers]
  [Include OI-01 / OI-03 status if touched]

ARTIFACTS CREATED:
  Path:
  Hash (BLAKE2b-256):

FAILED CHECKS:
  [NONE or description of failure + evidence path]

NEXT ACTION:
  [Single next step — one sentence]

KNOWN RISKS:
  [Any risks identified during this session]
```

---

## Usage Rules

```text
1. Fill template before ending session
2. Commit the filled packet to: PH6_CLOSEKIT/campaigns/<CXX>/
3. Do not leave open items undocumented
4. Hash all artifacts before recording
5. If campaign closed: also create RECEIPTS/C<XX>_CLOSURE_RECEIPT.md
```

---

## Closure Evidence Path

```text
PH6_SOURCE/EVIDENCE_CAMPAIGNS/RECEIPTS/C<XX>_CLOSURE_RECEIPT.md

Required fields:
  run_stamp:
  frame_count:
  replay_hash_match: PASS / FAIL
  human_signoff:
  date:
```

---

## Anti-Drift Reminder

```text
Do not carry forward unresolved assumptions.
Do not carry forward unverified claims.
Every open item must appear in OPEN ITEMS.
Every artifact must have a hash.
```
