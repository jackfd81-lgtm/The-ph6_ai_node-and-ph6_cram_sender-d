from ph6_l2_expand.lmpq_proposed.bench_four_experiences import run_four_experience_bench


def test_four_experiences_all_complete(tmp_path):
    result = run_four_experience_bench(tmp_path / "mram-s")

    assert set(result.keys()) == {
        "experience_1_normal_path",
        "experience_2_drop_loss_path",
        "experience_3_rehydration_path",
        "experience_4_provenance_continuity_path",
    }

    for name, exp in result.items():
        assert exp["violations"] == [], f"{name} produced boundary violations"
        assert exp["stages"]["bcv2_bundle_write"] == "WRITTEN", name


def test_experience_1_is_normal_path_only():
    import tempfile
    from pathlib import Path
    from ph6_l2_expand.lmpq_proposed.bench_four_experiences import _experience_1_normal_path

    with tempfile.TemporaryDirectory() as td:
        exp = _experience_1_normal_path(Path(td), 1_000_000)
    assert set(exp["stages"].keys()) == {"RT_VDT_VLT_normal_path", "bcv2_bundle_write"}


def test_experience_2_preserves_drop_not_delete():
    import tempfile
    from pathlib import Path
    from ph6_l2_expand.lmpq_proposed.bench_four_experiences import _experience_2_drop_loss_path

    with tempfile.TemporaryDirectory() as td:
        exp = _experience_2_drop_loss_path(Path(td), 2_000_000)
    assert exp["evidence_deleted_asserted_false"] is True


def test_experience_3_marks_replay_not_new_observation():
    import tempfile
    from pathlib import Path
    from ph6_l2_expand.lmpq_proposed.bench_four_experiences import _experience_3_rehydration_path

    with tempfile.TemporaryDirectory() as td:
        exp = _experience_3_rehydration_path(Path(td), 3_000_000)
    assert exp["aht_is_replay"] is True
    assert exp["aht_new_observation"] is False


def test_experience_4_has_provenance_and_continuity_hash():
    import tempfile
    from pathlib import Path
    from ph6_l2_expand.lmpq_proposed.bench_four_experiences import (
        _experience_4_provenance_continuity_path,
    )

    with tempfile.TemporaryDirectory() as td:
        exp = _experience_4_provenance_continuity_path(Path(td), 4_000_000)
    assert exp["soso_jedi_continuity_hash"]


def test_bench_is_deterministic_across_independent_runs(tmp_path):
    r1 = run_four_experience_bench(tmp_path / "run1")
    r2 = run_four_experience_bench(tmp_path / "run2")

    for name in r1:
        assert r1[name]["bcv2_bundle_id"] == r2[name]["bcv2_bundle_id"], name
