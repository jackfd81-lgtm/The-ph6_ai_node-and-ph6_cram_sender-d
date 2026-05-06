"""
TOK-1.0 Prune Scheduler

Lane: 2
Authority: ZERO
Write domain: MRAM-S only (via TokenStore)

Orchestrates deterministic prune cycles.
TOK does not self-govern — PH6 runtime calls run_prune_cycle().
No background daemons.
No autonomous scheduling.
"""

from __future__ import annotations

from typing import Optional


def should_run_prune(
    last_prune_ms: int,
    config: dict,
    current_time_ms: int,
) -> bool:
    """Return True if enough time has elapsed since the last prune."""
    interval_ms = config.get("prune_interval_seconds", 60) * 1000
    return (current_time_ms - last_prune_ms) >= interval_ms


def run_prune_cycle(
    store,
    config: dict,
    current_time_ms: Optional[int] = None,
) -> int:
    """
    Run one deterministic prune pass on the given TokenStore.

    Returns the number of tokens pruned.
    PH6 runtime is responsible for calling this — TOK does not self-schedule.
    """
    from ph6.tok.lifecycle import now_ms

    ts = current_time_ms if current_time_ms is not None else now_ms()
    return store.prune(config, current_time_ms=ts)


def compute_next_prune_ms(last_prune_ms: int, config: dict) -> int:
    """Return the earliest timestamp at which the next prune should run."""
    interval_ms = config.get("prune_interval_seconds", 60) * 1000
    return last_prune_ms + interval_ms
