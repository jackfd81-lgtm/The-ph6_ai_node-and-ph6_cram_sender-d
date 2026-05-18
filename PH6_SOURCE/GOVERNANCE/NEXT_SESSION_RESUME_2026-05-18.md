# PH6 / CRAM — Next Session Resume Note

## Current State

PH6 is paused after bounded production-clearance seal creation.

## Canonical Read-First File

PH6_SOURCE/GOVERNANCE/PH6_PRODUCTION_CLEARANCE_SEAL_2026-05-18.md

## Current Clearance

Bounded production clearance declared for the single-node main_pi evidence instrument and cross-node RSYNC hash-continuity export.

Declaration ID: PH6-PROD-CLEAR-2026-05-18-001
Declaration commit: 11966dee72
Seal commit: 1be60d06b4

## On Hold

Hailo integration remains on hold (OI-01 DESCOPED, future revision only).

## Next Hardware Step

Raspberry Pi 3B+ hookup / integration preparation.

## Next Session Should Start With

1. Read the production clearance seal.
2. Confirm repository clean state.
3. Confirm governance scan PASS.
4. Prepare Pi 3B+ role plan (Authority / Worker / Export / Monitor / Test Node).
5. Do not expand authority.
6. Do not start Hailo.
7. Do not modify PASS/DROP, CRAM-A, RSYNC, or Lane 1 authority without explicit operator approval.

## Hard Guardrails

- Lane 1 remains sole authority.
- Lane 2 remains advisory only.
- PSEUDO-A remains PASS/DROP authority.
- CRAM-A remains authoritative storage.
- RSYNC remains Priority Zero.
- No remote PASS/DROP authority.
- No remote CRAM-A write authority.
- No distributed authority.
- No multi-writer CRAM.
- No Hailo integration.
