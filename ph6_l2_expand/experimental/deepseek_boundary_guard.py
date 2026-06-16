"""
ph6_l2_expand.experimental.deepseek_boundary_guard

Lane: 2
Authority: ZERO
Write domain: none (pure scan)

DeepSeek-specific wrapper around ph6_l2_expand.boundary_guard. Real
language models are non-deterministic and may emit verdict-like language
even when explicitly told not to. This module is the last check before a
DeepSeek-derived advisory record is handed to mram_s_writer, which will
quarantine the *entire* record (never sanitize) if anything here -- or in
the wrapped record -- trips boundary_guard.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ph6_l2_expand.boundary_guard import classify, scan

# How much of a raw model response to retain for transparency/audit.
RAW_RESPONSE_EXCERPT_CHARS = 2000


def check_raw_response(raw_text: str) -> Tuple[str, List[str]]:
    """Classify raw (pre-JSON-parse) model output text."""
    return classify(raw_text)


def excerpt(raw_text: str) -> str:
    return raw_text[:RAW_RESPONSE_EXCERPT_CHARS]


def check_advisory(advisory: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Classify a fully-built advisory dict before it is wrapped for MRAM-S."""
    return classify(advisory)


__all__ = ["check_raw_response", "check_advisory", "excerpt", "scan", "classify"]
