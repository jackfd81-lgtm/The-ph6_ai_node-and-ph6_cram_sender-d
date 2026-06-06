#!/usr/bin/env python3
"""
PH6 Governor — wraps governance_drift_scan.py with --scan flag.
Canonical scan root: PH6_SOURCE/ (never /home/jack).
PROPOSED artifact. Ratified_by: null.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_ROOT = REPO_ROOT
SCANNER = Path("/home/jack/PH6_SOURCE/TOOLS/governance_drift_scan.py")

PROPOSED_BY = "claude-code-lane2"


def run_scan(extra_args: list) -> int:
    if not SCANNER.exists():
        print(f"GOVERNOR: scanner not found at {SCANNER}")
        print("  STATUS: DEGRADED — install governance_drift_scan.py to reach PASS")
        return 1

    cmd = [sys.executable, str(SCANNER), "--scan-root", str(SCAN_ROOT)] + extra_args
    print(f"GOVERNOR: running scan")
    print(f"  scanner  : {SCANNER}")
    print(f"  root     : {SCAN_ROOT}")
    print(f"  command  : {' '.join(str(c) for c in cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] == "--scan":
        extra = args[1:] if args else []
        return run_scan(extra)

    if args[0] in ("-h", "--help"):
        print("ph6_governor.py --scan [extra args passed to drift scanner]")
        print("Canonical scan root: PH6_SOURCE/")
        print("Expected: 0 CRITICAL / 0 HIGH / 0 WARN")
        return 0

    print(f"GOVERNOR: unknown argument {args[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
