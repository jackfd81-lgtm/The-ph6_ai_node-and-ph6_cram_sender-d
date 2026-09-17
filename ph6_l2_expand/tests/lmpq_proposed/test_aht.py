import json

import pytest

from ph6_l2_expand.lmpq_proposed.tokens import make_aht, rehydrate_token_from_chain


def _make_store_with_vlt(tmp_path, suffix="aht_test"):
    from ph6.tok.lifecycle import TokenStore
    from ph6_l2_expand.lmpq_proposed._shared import build_promoted_vlt

    tokens_dir = tmp_path / "tokens"
    store = TokenStore(str(tokens_dir))
    vlt = build_promoted_vlt(store, 2_000_000, "cram_ref_aht", suffix=suffix)
    return tokens_dir, vlt


def test_valid_aht_rehydration(tmp_path):
    tokens_dir, vlt = _make_store_with_vlt(tmp_path)
    audit_path = tokens_dir / "tok_advisory_audit.jsonl"

    aht = make_aht(audit_path, vlt.token_id, reconstructed_at_ms=9_999_999)

    assert aht.token_type == "AHT"
    assert aht.source_token_id == vlt.token_id
    assert aht.is_replay is True
    assert aht.new_observation is False
    # event_time_ms is the audit chain's own event time for the promotion
    # (event_time_ms=2_000_000+600 passed to promote_to_vlt in _shared.py),
    # not the VLT dataclass's internal timestamp_ms field.
    assert aht.event_time_ms == 2_000_600
    assert aht.reconstructed_at_ms == 9_999_999


def test_aht_hash_is_deterministic_across_wall_clock_times(tmp_path):
    """Replaying the same chain at different reconstructed_at_ms must not
    change reconstructed_state_hash or token_id (fixes the wall-clock
    nondeterminism pattern found in ph6_l2_expand/token_types.py)."""
    tokens_dir, vlt = _make_store_with_vlt(tmp_path)
    audit_path = tokens_dir / "tok_advisory_audit.jsonl"

    aht_1 = make_aht(audit_path, vlt.token_id, reconstructed_at_ms=1)
    aht_2 = make_aht(audit_path, vlt.token_id, reconstructed_at_ms=999_999_999)

    assert aht_1.token_id == aht_2.token_id
    assert aht_1.reconstructed_state_hash == aht_2.reconstructed_state_hash
    assert aht_1.reconstructed_at_ms != aht_2.reconstructed_at_ms


def test_aht_rejects_missing_source_token(tmp_path):
    tokens_dir, _vlt = _make_store_with_vlt(tmp_path)
    audit_path = tokens_dir / "tok_advisory_audit.jsonl"

    with pytest.raises(ValueError, match="invalid rehydration reference"):
        make_aht(audit_path, "token_that_never_existed", reconstructed_at_ms=1)


def test_aht_rejects_missing_audit_chain(tmp_path):
    with pytest.raises(ValueError):
        make_aht(tmp_path / "no_such_chain.jsonl", "any_token", reconstructed_at_ms=1)


def test_aht_rejects_tampered_audit_chain(tmp_path):
    tokens_dir, vlt = _make_store_with_vlt(tmp_path)
    audit_path = tokens_dir / "tok_advisory_audit.jsonl"

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["payload"]["cram_ref_hash"] = "TAMPERED_EVIDENCE"
    lines[0] = json.dumps(tampered)
    audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="integrity"):
        make_aht(audit_path, vlt.token_id, reconstructed_at_ms=1)


def test_rehydrate_token_from_chain_returns_last_known_state(tmp_path):
    tokens_dir, vlt = _make_store_with_vlt(tmp_path)
    audit_path = tokens_dir / "tok_advisory_audit.jsonl"

    rehydrated = rehydrate_token_from_chain(audit_path, vlt.token_id)
    assert rehydrated["source_token_id"] == vlt.token_id
    assert rehydrated["last_event_type"] == "VDT_PROMOTED_TO_VLT"


def test_aht_no_forbidden_vocabulary(tmp_path):
    from ph6_l2_expand.boundary_guard import classify

    tokens_dir, vlt = _make_store_with_vlt(tmp_path)
    audit_path = tokens_dir / "tok_advisory_audit.jsonl"
    aht = make_aht(audit_path, vlt.token_id, reconstructed_at_ms=1)

    status, violations = classify(aht.to_dict())
    assert status == "OK", violations
