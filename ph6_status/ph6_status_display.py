#!/usr/bin/env python3
import json, time, sys
from pathlib import Path

STATUS_PATH = Path.home() / "ph6_status/status.json"

_C = {
    "BOOT":     "\033[90m",
    "CHECKING": "\033[33m",
    "WORKING":  "\033[32m",
    "THINKING": "\033[36m",
    "DONE":     "\033[34m",
    "ERROR":    "\033[31m",
}
RESET = "\033[0m"

print(f"PH6 Status Monitor — {STATUS_PATH}", flush=True)
print("─" * 60, flush=True)

while True:
    try:
        s = json.loads(STATUS_PATH.read_text())
        st = s.get("status", "?")
        color = _C.get(st, "")
        line = (
            f"\r{color}[{st:<8}]{RESET}  "
            f"cam={s.get('cam','?'):<8}"
            f"cram={s.get('cram','?'):<8}"
            f"ai={s.get('ai','?'):<10}"
            f"fps={s.get('fps',0):<6}"
            f"f={s.get('frame',0)}"
        )
        print(line, end="", flush=True)
    except FileNotFoundError:
        print("\r[WAITING] status.json not found", end="", flush=True)
    except Exception as e:
        print(f"\r[ERROR] {e}", end="", flush=True)
    time.sleep(0.5)
