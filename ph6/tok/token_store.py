"""
TOK-1.0 Token Store

Lane: 2
Authority: ZERO
Write domain: MRAM-S only

Live materialization store for RT, VDT, and VLT tokens.
Rebuildable from advisory audit chain.
Not authoritative truth.
"""

from ph6.tok.lifecycle import (
    TokenStore,
    RT,
    VDT,
    VLT,
    TokenBase,
    DEFAULT_TOK_CONFIG,
    attempt_vdt_promotion,
    should_prune_vdt,
    should_prune_vlt,
)

__all__ = [
    "TokenStore",
    "RT",
    "VDT",
    "VLT",
    "TokenBase",
    "DEFAULT_TOK_CONFIG",
    "attempt_vdt_promotion",
    "should_prune_vdt",
    "should_prune_vlt",
]
