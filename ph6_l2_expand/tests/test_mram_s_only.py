import json

from ph6_l2_expand.mram_s_writer import write_advisory
from ph6_l2_expand.schemas import ADVISORY_AUTHORITY_LEVEL, MRAM_S_ADVISORY_SCHEMA


def _record(source_object_id="internal_000001", analysis_type="TOKEN", advisory_data=None):
    return {
        "schema": MRAM_S_ADVISORY_SCHEMA,
        "advisory_id": "00000000-0000-0000-0000-000000000001",
        "source_object_id": source_object_id,
        "analysis_type": analysis_type,
        "created_at": "2026-06-14T00:00:00Z",
        "authority_level": ADVISORY_AUTHORITY_LEVEL,
        "isolation_confirmed": True,
        "refs": [source_object_id],
        "advisory_data": advisory_data or {},
    }


def test_write_advisory_lands_under_out_dir(mram_s_dir):
    path, status, violations = write_advisory(mram_s_dir, "record.json", _record())
    assert status == "WRITTEN"
    assert violations == []
    assert path.is_relative_to(mram_s_dir)
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk["schema"] == MRAM_S_ADVISORY_SCHEMA
    assert on_disk["authority_level"] == "ZERO"


def test_canonical_json_is_sorted_and_compact(mram_s_dir):
    path, _, _ = write_advisory(mram_s_dir, "record.json", _record())
    raw = path.read_bytes().decode("utf-8")
    assert ", " not in raw
    assert ": " not in raw


def test_atomic_write_leaves_no_tmp_files(mram_s_dir):
    write_advisory(mram_s_dir, "record.json", _record())
    leftovers = list(mram_s_dir.glob("*.tmp"))
    assert leftovers == []
