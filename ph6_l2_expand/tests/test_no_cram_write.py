import pytest

from ph6_l2_expand.mram_s_writer import MRAMSWriteError, resolve_target, write_advisory
from ph6_l2_expand.schemas import ADVISORY_AUTHORITY_LEVEL, MRAM_S_ADVISORY_SCHEMA


def _record():
    return {
        "schema": MRAM_S_ADVISORY_SCHEMA,
        "advisory_id": "00000000-0000-0000-0000-000000000002",
        "source_object_id": "internal_000001",
        "analysis_type": "TOKEN",
        "created_at": "2026-06-14T00:00:00Z",
        "authority_level": ADVISORY_AUTHORITY_LEVEL,
        "isolation_confirmed": True,
        "refs": ["internal_000001"],
        "advisory_data": {},
    }


@pytest.mark.parametrize("out_dir", ["/var/ph6/cram-0", "/var/ph6/cram-a", "/var/ph6/cram-r"])
def test_resolve_target_refuses_cram_dirs(out_dir):
    with pytest.raises(MRAMSWriteError):
        resolve_target(out_dir, "record.json")


def test_resolve_target_refuses_cram_segment_in_filename(mram_s_dir):
    with pytest.raises(MRAMSWriteError):
        resolve_target(mram_s_dir, "cram-a/record.json")


def test_resolve_target_refuses_traversal(mram_s_dir):
    with pytest.raises(MRAMSWriteError):
        resolve_target(mram_s_dir, "../escape.json")


def test_resolve_target_refuses_absolute_filename(mram_s_dir):
    with pytest.raises(MRAMSWriteError):
        resolve_target(mram_s_dir, "/etc/passwd")


def test_write_advisory_never_lands_in_cram(mram_s_dir):
    path, status, _ = write_advisory(mram_s_dir, "record.json", _record())
    assert status == "WRITTEN"
    parts_lower = [p.lower() for p in path.parts]
    assert "cram-0" not in parts_lower
    assert "cram-a" not in parts_lower
    assert "cram-r" not in parts_lower
