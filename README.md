# PH6

PH6 is a measurement system for a Raspberry Pi. It takes in sensor frames (camera, audio, ESP sensors), checks each one with fixed, repeatable rules, and keeps a tamper-evident record of what it saw. Every stored record is hashed with BLAKE2b-256, and a frame is either kept (PASS) or rejected (DROP). Nothing else decides that.

There are two kinds of code in this repo:

- **Lane 1 (deterministic).** The capture and CRAM code under `ph6/cram_pu/`. Only this code may decide PASS or DROP and write the authority store (CRAM-A).
- **Lane 2 (advisory).** The swarm/token code under `ph6/ssmt/`, `ph6/tok/`, `ph6/research_agent/` and `ph6_l2_expand/`. It reads Lane 1 output and writes notes about it. It has **zero authority**: it cannot change a verdict, write CRAM-A, or affect RSYNC export.

The rules this repo is governed by live in `PH6_SOURCE/` (canon, schemas, governance). `CLAUDE.md` is the short version for AI assistants.

## Layout

| Path | What it is |
|---|---|
| `ph6/cram_pu/` | Capture, validation, replay, transfer, test drivers (Lane 1) |
| `ph6/ssmt/` | Advisory swarm worker and its socket client (Lane 2) |
| `ph6/tok/` | Advisory token lifecycle and CRAM reconciliation (Lane 2) |
| `ph6/advisory_chain.py` | Shared append-only audit chain with checkpoints |
| `ph6/measurement_record.py` | Measurement record schema helpers |
| `ph6/interface/` | Local desktop/fleet UI |
| `ph6_l2_expand/` | Further Lane 2 experiments (ratified top-level exception) |
| `PH6_SOURCE/` | Canon documents; scanned by the governance check |
| `pytest.ini` | Test configuration |

## Install on a Pi

Tested on a Raspberry Pi 5, Debian 13 (trixie), Python 3.13.5.

```bash
git clone https://github.com/jackfd81-lgtm/The-ph6_ai_node-and-ph6_cram_sender-d.git ph6-repo
cd ph6-repo
python3 -m venv ~/ph6-venv
~/ph6-venv/bin/pip install pytest==9.2.0 PyYAML==6.0.2 numpy==2.2.4 \
    opencv-python-headless==4.10.0.84 jsonschema==4.19.2
```

These versions are the ones the test suite was last run with. PyYAML, numpy, OpenCV and jsonschema match the Debian system packages on the Pi.

## Run the tests

From the repo root:

```bash
~/ph6-venv/bin/python -m pytest -q -p no:cacheprovider
```

Tests write only to pytest's temporary directory. To be certain a run cannot touch a live install, run it in a throwaway user scope where only one scratch folder is writable:

```bash
mkdir -p ~/ph6-scratch/run ~/ph6-scratch/t
systemd-run --user --quiet --wait --pipe --collect \
  -p WorkingDirectory=$PWD -p PrivateUsers=yes -p ProtectSystem=strict \
  -p ProtectHome=read-only -p ReadWritePaths=$HOME/ph6-scratch \
  -p PrivateTmp=yes -p PrivateNetwork=yes -p NoNewPrivileges=yes \
  -p InaccessiblePaths=-/run/user/$(id -u)/ph6-advisory -p ReadOnlyPaths=-/var/ph6 \
  -E XDG_RUNTIME_DIR=$HOME/ph6-scratch/run -E TMPDIR=$HOME/ph6-scratch/t \
  -E PYTHONDONTWRITEBYTECODE=1 \
  ~/ph6-venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=$HOME/ph6-scratch/pt
```

The repo itself must be inside `~/ph6-scratch`, or pytest will not be able to read it under `ProtectHome=read-only`. Move the clone there, or add its path to `ReadWritePaths`.

## The advisory worker

`ph6/ssmt/worker.py` runs as a user systemd service (`ph6-advisory.service`, installed at `~/.config/systemd/user/`; the unit file is not yet in this repo). Capture code sends it a small JSON notice over a local Unix datagram socket after each CRAM commit. The worker runs nine advisory swarms and writes snapshots and an audit log under its own MRAM-S folder. If it is configured with `--cram-store`, it also reads those CRAM stores to build continuity tokens.

**What it can do**

- Read the CRAM stores it is pointed at.
- Write advisory snapshots, tokens, a coverage database and audit logs under its `--root` folder.

**What it cannot do**

- Change a PASS/DROP verdict or write CRAM-A. Every packet it emits is labelled `authority: NONE`, `lane: LANE_2_ADVISORY`, with all `affects_*` flags false.
- Accept input that carries extra fields. The decoder takes exactly `cram_ref`, `cram_packet_hash` and `tok_refs`, and rejects anything else.
- Use an advisory folder that overlaps a CRAM store. The reconciler refuses to start.
- Reply to or block the sender. Delivery is best effort; if the worker is down or the queue is full, the sender gets `False` and carries on.
- Run without limits when started with `--require-limits`. It refuses to start unless the kernel enforces CPU ≤ 30%, memory ≤ 512 MB and swap = 0.
- Reach the network, or write anywhere except its own folder, when run under the provided unit (`RestrictAddressFamilies=AF_UNIX`, `ProtectSystem=strict`, `ProtectHome=read-only`, a single `ReadWritePaths`). These limits come from systemd, not from the Python code. Run outside the unit, the worker has the full permissions of its user.

See `ph6/ssmt/ASYNC_RUNTIME.md` and `ph6/tok/CONTINUITY_V03.md` for details.

## Status

Everything in this repo is a working state under operator review. Open stop-ship items, such as the Hailo hardware run and the Pi-to-Pi live transfer proof, are tracked in `PH6_SOURCE/GAP_REGISTER_v3.0.md`.

<!-- {"proposed_by":"claude-code-lane2","proposed_at_utc":"2026-11-22T00:20:00Z","api_call_log_ref":"ph6_review_phase2_20261121","ratified_by":null} -->
