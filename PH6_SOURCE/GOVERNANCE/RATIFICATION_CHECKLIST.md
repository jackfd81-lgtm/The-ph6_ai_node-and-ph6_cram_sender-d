# PH6 Ratification Checklist

**Purpose:** Required checks before any commit is ratified.  
**Authority:** ZERO — operator must manually verify and sign off.  
**Lane:** 2 (advisory — operator completes, not AI)

Copy this checklist and mark each item. Do not ratify until all required items are checked.

---

## Required (Block commit if any unchecked)

```
[ ] Restore point created
    bash PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/create_desktop_restore_point.sh
    Verify: restore_points/LAST_KNOWN_GOOD_MANIFEST.json exists

[ ] Desktop syntax PASS
    python3 -m py_compile PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/ph6_windows_terminal_display.py

[ ] Scanner syntax PASS
    python3 -m py_compile PH6_SOURCE/TOOLS/governance_drift_scan.py

[ ] Guard regression tests PASS
    python3 PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/test_desktop_status_guards.py
    Required: 0 failures

[ ] Governance canonical scan PASS (0 CRITICAL / 0 HIGH / 0 WARN)
    python3 PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root /home/jack/PH6_SOURCE
    Required: result = PASS, critical=0, high=0, warn=0

[ ] CRAM harness PASS
    python3 /home/jack/ph6/cram_pu/ph6_internal_test.py
    Required: 20/20 checks, known-good hash = 014652358db408cf...

[ ] Git diff reviewed
    git -C /home/jack diff --stat HEAD
    Operator must have read the diff and understood all changes

[ ] No authority boundary changed
    Verify: no writes to CRAM-A, canon, evidence chain, audit.jsonl from new code
    Verify: no auto-commit or auto-push added to any script

[ ] No auto commit/push added
    grep -r "git commit" PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/ must return empty
    grep -r "git push"   PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/ must return empty

[ ] Operator ratified
    Operator has read this checklist, reviewed all output above, and explicitly approves
```

---

## Advisory (Non-blocking, but record state)

```
[ ] INFO hit count within budget (current budget: <= 30)
    governance scan --scan-root /home/jack/PH6_SOURCE: info count = ____

[ ] Desktop UI layout unchanged
    TC_MENU_IDX still = 3
    FB_MENU_IDX still = 8
    No menus renumbered
    Stop logic (X=SIGINT, FORCE=SIGKILL) unchanged

[ ] Standards crosswalk present
    PH6_SOURCE/GOVERNANCE/PH6_STANDARDS_CROSSWALK.md exists

[ ] Courtroom evidence readiness present
    PH6_SOURCE/GOVERNANCE/PH6_COURTROOM_EVIDENCE_READINESS.md exists

[ ] Command registry policy present
    PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/command_registry_policy.json exists

[ ] Workstation priority doctrine present
    PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/PH6_WORKSTATION_PRIORITY.md exists
```

---

## Governance Budgets (Prototype Phase)

| Severity | Required | Budget |
|---------|---------|--------|
| CRITICAL | 0 | Hard block |
| HIGH | 0 | Hard block |
| WARN | 0 | Soft block — requires explanation |
| INFO | ≤ 30 | Acceptable during prototype |
| INFO > 30 | — | Requires classification update |
| INFO > 50 | — | Requires cleanup sprint |

---

## Storage Doctrine Reminder

```
Git = prototype source control layer (code history only)
CRAM = evidence preservation authority
Manifests = artifact inventory
Operator log = custody record
```

Git commit history is NOT the chain of custody. Evidence authority comes from CRAM chain, artifact manifests, hashes, replay records, and operator logs. These must survive and remain valid independent of git.

---

## Workstation Class Reminder

```
Class 1 — Cloud Terminal / Claude Terminal  →  ratify here
Class 2 — SSH Terminal                      →  execute commit here
Class 3 — PH6 Desktop Interface            →  observe only, no commit
```

Never commit from inside the desktop terminal.

---

*Lane-2 advisory document. Operator must complete independently. AI cannot ratify.*
