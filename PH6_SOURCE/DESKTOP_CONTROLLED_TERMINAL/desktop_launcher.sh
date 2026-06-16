#!/bin/bash
# PH6 Desktop Controlled Terminal launcher

TERMINAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_TERMINAL="/home/jack/PH6_SOURCE/DESKTOP_CONTROLLED_TERMINAL/ph6_desktop_terminal.py"

if [ ! -f "$PROJECT_TERMINAL" ]; then
  echo "ERROR: PH6 desktop terminal not found:"
  echo "$PROJECT_TERMINAL"
  exit 1
fi

MODE="${1:---windows}"

case "$MODE" in
  --windows)
    exec python3 "$PROJECT_TERMINAL" --windows
    ;;
  --classic)
    exec python3 "$PROJECT_TERMINAL" --classic
    ;;
  --help|-h)
    echo "PH6 Desktop Controlled Terminal"
    echo
    echo "Usage:"
    echo "  desktop            Open Windows-style terminal"
    echo "  desktop --windows  Open Windows-style terminal"
    echo "  desktop --classic  Open classic terminal"
    echo "  desktop --help     Show help"
    exit 0
    ;;
  *)
    echo "Unknown option: $MODE"
    echo "Use: desktop --help"
    exit 2
    ;;
esac
