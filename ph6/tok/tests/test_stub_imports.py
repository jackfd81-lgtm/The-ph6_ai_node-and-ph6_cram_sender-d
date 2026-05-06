"""
TOK-1.0 stub import path verification.
Proves all Section 20 modules are importable and Authority ZERO.
"""

import importlib


STUB_MODULES = [
    "ph6.tok.lifecycle",
    "ph6.tok.geometry",
    "ph6.tok.reconstruct",
    "ph6.tok.scheduler",
    "ph6.tok.rebuild",
    "ph6.tok.validators",
    "ph6.tok.audit_writer",
    "ph6.tok.token_store",
]


def test_all_stubs_importable():
    for mod_name in STUB_MODULES:
        mod = importlib.import_module(mod_name)
        assert mod is not None, f"Failed to import {mod_name}"


def test_geometry_functions_exist():
    from ph6.tok.geometry import bbox_iou, meets_spatial_consistency, compute_centroid
    assert callable(bbox_iou)
    assert callable(meets_spatial_consistency)
    assert callable(compute_centroid)


def test_geometry_iou_deterministic():
    from ph6.tok.geometry import bbox_iou
    a = [0.0, 0.0, 10.0, 10.0]
    assert bbox_iou(a, a) == 1.0
    assert bbox_iou(a, [100.0, 100.0, 10.0, 10.0]) == 0.0


def test_validators_authority_zero():
    from ph6.tok.validators import validate_config
    from ph6.tok.lifecycle import DEFAULT_TOK_CONFIG
    errors = validate_config(DEFAULT_TOK_CONFIG)
    assert errors == [], f"DEFAULT_TOK_CONFIG failed validation: {errors}"


def test_scheduler_functions_exist():
    from ph6.tok.scheduler import should_run_prune, run_prune_cycle, compute_next_prune_ms
    assert callable(should_run_prune)
    assert callable(run_prune_cycle)
    assert callable(compute_next_prune_ms)


def test_scheduler_interval_logic():
    from ph6.tok.scheduler import should_run_prune
    config = {"prune_interval_seconds": 60}
    assert not should_run_prune(1000, config, 50000)
    assert should_run_prune(1000, config, 62000)


def test_reconstruct_functions_exist():
    from ph6.tok.reconstruct import (
        validate_chain_integrity,
        count_events_by_type,
        reconstruct_and_emit_receipt,
    )
    assert callable(validate_chain_integrity)
    assert callable(count_events_by_type)
    assert callable(reconstruct_and_emit_receipt)


def test_audit_writer_exports():
    from ph6.tok.audit_writer import AdvisoryAudit, blake2b256_hex
    assert AdvisoryAudit is not None
    assert callable(blake2b256_hex)


def test_token_store_exports():
    from ph6.tok.token_store import TokenStore, RT, VDT, VLT, DEFAULT_TOK_CONFIG
    assert TokenStore is not None
    assert RT is not None
    assert VDT is not None
    assert VLT is not None
