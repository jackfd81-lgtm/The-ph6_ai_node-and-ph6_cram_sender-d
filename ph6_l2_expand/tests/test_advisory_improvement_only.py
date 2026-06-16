from pathlib import Path

from ph6_l2_expand.experimental.advisory_improvement_tracker import MOCK_OFFLINE_AI, run_cycles
from ph6_l2_expand.workers.audit_worker import run_audit


def test_improvement_cycles_write_only_mram_s(mram_s_dir, sample_source_object):
    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=5, mode=MOCK_OFFLINE_AI)

    assert len(results) == 5
    for r in results:
        assert r["status"] == "WRITTEN"
        # every written file is inside mram_s_dir
        assert Path(r["path"]).is_relative_to(mram_s_dir)


def test_improvement_metrics_are_advisory_topology_only(mram_s_dir, sample_source_object):
    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=5, mode=MOCK_OFFLINE_AI)

    for r in results:
        metrics = r["metrics"]
        assert set(metrics.keys()) == {
            "rt_count", "vdt_count", "vlt_count",
            "stable_link_count", "decayed_link_count", "topology_density",
        }
        # topology_density formatted to 4 decimals
        float(metrics["topology_density"])
        assert len(metrics["topology_density"].split(".")[1]) == 4


def test_audit_of_improvement_output_is_clean(mram_s_dir, sample_source_object):
    run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=5, mode=MOCK_OFFLINE_AI)

    report = run_audit(mram_s_dir)
    assert report["status"] == "OK"
    assert report["scanned"] == 5
    assert report["quarantined"] == 0


def test_records_never_reference_cram_or_evidence_packet(mram_s_dir, sample_source_object):
    results = run_cycles("internal_000001", sample_source_object, mram_s_dir, cycles=3, mode=MOCK_OFFLINE_AI)

    for r in results:
        text = open(r["path"], "r", encoding="utf-8").read()
        assert "cram-0" not in text.lower()
        assert "cram-a" not in text.lower()
        assert "cram-r" not in text.lower()
        assert "evidencepacket" not in text.lower()
