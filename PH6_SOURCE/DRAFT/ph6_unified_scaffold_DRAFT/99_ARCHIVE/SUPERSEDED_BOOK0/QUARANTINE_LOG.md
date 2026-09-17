Document Type: Quarantine Log
Status: DRAFT — NOT RATIFIED
Version: 0.2 (supersedes the framing in this same folder's NOTICE.md v0.1)
Authority: Lane 2 advisory/build output only
Ratification: NONE

# Quarantine Log — BOOK 0 variant

## Correction to my earlier framing
The previous version of this notice (still readable in `NOTICE.md`) called
this file "superseded" and treated the 86,844-byte `01_DOCTRINE_AND_SPEC`
copy as the obvious canonical one because it has more extractable text.
That's a size/completeness judgment I made — not something established by
any authoritative PH6 source. Per stricter quarantine-classification
discipline: **that basis is not sufficient to classify this as a resolved
duplicate.** Correcting the record rather than leaving it standing unflagged.

## Candidate artifact
- Original path: `PH6_SOURCE_SORTED/01_CORE_DOCTRINE/Six engines pH 6/BOOK 0 — INTERPRETIVE CONTROL PLANE.pdf`
- Quarantined to: `99_ARCHIVE/SUPERSEDED_BOOK0/BOOK 0 — INTERPRETIVE CONTROL PLANE.pdf` (filename unchanged)
- Size: 642,968 bytes | Pages: 4
- BLAKE2b-256: see `06_AUDIT_AND_LOGS/migration_reconciliation_record.json`

## Candidate canonical counterpart
- Path: `01_DOCTRINE_AND_SPEC/BOOK 0 — INTERPRETIVE CONTROL PLANE.pdf`
- Size: 86,844 bytes | Pages: 4

## Classification basis (what I actually have, no more)
- Both files: identical filename, identical page count (4).
- Extracted text differs sharply: ~23 lines (mostly bullet glyphs, reads as
  a slide/outline export) vs. ~136 lines of numbered doctrine (`B0 §0`...).
  Verified by direct `pdftotext`/`pdfinfo` run, not inference from metadata.
- No PH6 source document in anything uploaded this session states which of
  the two is authoritative, or that one supersedes the other.

## Classification result
**UNRESOLVED_QUARANTINE_CLASSIFICATION.**
The file is physically separated (moved to `99_ARCHIVE/`) so it stops
colliding with the same filename in a live doctrine folder, but that is a
housekeeping move, not a supersession ruling. It has not been destroyed,
edited, or renamed. Lane 1 needs to either (a) confirm the 86,844-byte
copy as canonical and this one as formally superseded, or (b) say the two
serve different purposes (e.g., one really is an outline/slide companion
to the other) and both stay.
