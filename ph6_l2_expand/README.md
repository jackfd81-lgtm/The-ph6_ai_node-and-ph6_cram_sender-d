# ph6_l2_expand — SoSo Token + Virtual Token Mapping (Book V experimental)

**Lane: 2 — Authority: ZERO — Write domain: MRAM-S only**

> WARNING: This subsystem is Book V experimental, Lane 2 only, MRAM-S only,
> Authority ZERO. It must never be imported by, or coupled to, Lane-1
> modules (CRAM-0, PSEUDO-M, PSEUDO-A, CRAM-A, CRAM-R, EvidencePacket,
> replay authority path, authority-chain state, thresholds, PASS/DROP).

## Purpose

This package implements an advisory SoSo token and virtual-token mapping
subsystem used to:

- represent observed CRAM-A / CRAM-R reference objects as Reference Tokens
  (RT)
- generate advisory hypotheses about relationships between those objects
  as Virtual Decay Tokens (VDT)
- promote stable, repeatedly-reinforced VDTs to Virtual Longevity Tokens
  (VLT)
- track whether advisory topology "improves" (more stable links, clearer
  decay/stability classification, repeatable topology) across repeated
  cycles — entirely within MRAM-S
- exercise the above using a deterministic mock offline AI by default, or
  an optional local Ollama `deepseek-r1:1.5b` model

## Authority boundary

```
Reality
  -> CRAM-0
  -> PSEUDO-M
  -> PSEUDO-A
  -> CRAM-A / CRAM-R
  -> read-only reference seed
  -> SoSo / Tokens / Mock AI / DeepSeek   (this package)
  -> MRAM-S only
```

- Lane 2 may **read** CRAM-A / CRAM-R **read-only** (as a reference seed,
  via `workers/reference_worker.py`).
- Lane 2 may **write MRAM-S only** (via `mram_s_writer.py`, which refuses
  any path containing a `cram-0`, `cram-a`, or `cram-r` segment and
  refuses path traversal).
- Lane 2 **never** influences thresholds, PASS/DROP verdicts,
  EvidencePacket, replay dependency, or authority-chain state.
- SoSo and tokens begin only **after** Lane-1 adjudication is complete.
  They are advisory topology only.

### Locked token classes

Only three token classes exist:

- **RT**  — Reference Token
- **VDT** — Virtual Decay Token
- **VLT** — Virtual Longevity Token

### Boundary guard

`boundary_guard.py` scans every advisory payload for forbidden
authority-language (`PASS`, `DROP`, `ACCEPT`, `REJECT`, `PROMOTE`,
`verdict`, `threshold`, `EvidencePacket`, "modify CRAM/PSEUDO/replay/gate",
etc.). Any hit classifies the **entire** payload `DRIFT_FAIL` and
`mram_s_writer.py` writes it to `<out>/quarantine/` unchanged — it is
never sanitized into accepted output.

## Mock offline AI (default)

`experimental/mock_ai_client.py` is a deterministic, rule-based, fully
offline advisory node (`MOCK_OFFLINE_AI`). Same input always produces the
same output. It requires no internet and no Ollama, and is the default
for every CLI command.

## Optional local DeepSeek (experimental)

`experimental/deepseek_client.py` can call a local Ollama instance running
`deepseek-r1:1.5b` (`http://127.0.0.1:11434/api/generate`, `temperature=0`,
`top_p=1`, enforced timeout and prompt-size limits). If Ollama is
unreachable or returns unparseable output, it degrades safely to a
`SKIPPED_DEEPSEEK_OFFLINE` advisory record — it never fails Lane 1 or
blocks RSYNC, and it never silently falls back to the mock AI.

## Install / run notes

No third-party dependencies. Python 3.9+. Run from the repository root
(`/home/jack`) so `ph6_l2_expand` is importable as `ph6.ph6_l2_expand`'s
sibling package under `ph6/`.

A "source object" is a small read-only JSON file representing a CRAM-A/R
reference object, e.g.:

```json
{
  "object_id": "internal_000001",
  "motion_fraction": 0.42,
  "rssi_event": "stable",
  "continuity_chain": "c01"
}
```

## CLI examples

```bash
python3 -m ph6_l2_expand.cli map --source object.json --out /var/ph6/mram-s/
python3 -m ph6_l2_expand.cli mock-ai --source object.json --out /var/ph6/mram-s/
python3 -m ph6_l2_expand.cli improve --source object.json --out /var/ph6/mram-s/ --cycles 5
python3 -m ph6_l2_expand.cli compare-maps --before before.json --after after.json
python3 -m ph6_l2_expand.cli deepseek --source object.json --out /var/ph6/mram-s/ --mode mock-offline-ai
python3 -m ph6_l2_expand.cli deepseek --source object.json --out /var/ph6/mram-s/ --mode ollama-local
python3 -m ph6_l2_expand.cli audit --out /var/ph6/mram-s/
```

## Tests

```bash
python3 -m pytest ph6_l2_expand/tests -q
```

Tests prove (among other things): SoSo/tokens are not Lane 1, no write
ever reaches CRAM-0/A/R, no PASS/DROP from mock AI or DeepSeek becomes
accepted output, replay works with `ph6_l2_expand` entirely absent, token
classes are locked to RT/VDT/VLT, and mock AI output is deterministic.
