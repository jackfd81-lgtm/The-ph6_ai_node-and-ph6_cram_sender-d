import json
import os

import pytest

from ph6.hw_hooks.advisory_log import (
    MRAM_S_ADVISORY_SUBPATH,
    AdvisoryLogPathError,
    append_advisory_record,
    resolve_advisory_log_path,
)

ADVISORY_RECORD = {
    "schema": "ph6.hw_hooks.pizero_heartbeat.v1",
    "authority": "ZERO",
    "non_authoritative": True,
    "node_id": "jackjack2",
}


def test_resolve_path_stays_within_mram_s_advisory_root(tmp_path):
    path = resolve_advisory_log_path(str(tmp_path), "zero2w_heartbeat.jsonl")
    expected_root = os.path.abspath(os.path.join(str(tmp_path), MRAM_S_ADVISORY_SUBPATH))
    assert path.startswith(expected_root)


def test_resolve_path_refuses_escape(tmp_path):
    with pytest.raises(AdvisoryLogPathError):
        resolve_advisory_log_path(str(tmp_path), "../../etc/passwd")


def test_append_writes_jsonl_under_mram_s(tmp_path):
    path = append_advisory_record(str(tmp_path), "zero2w_heartbeat.jsonl", ADVISORY_RECORD)
    assert MRAM_S_ADVISORY_SUBPATH in path
    with open(path, encoding="utf-8") as fh:
        lines = [json.loads(line) for line in fh if line.strip()]
    assert lines == [ADVISORY_RECORD]


def test_append_is_append_only(tmp_path):
    append_advisory_record(str(tmp_path), "log.jsonl", ADVISORY_RECORD)
    second = dict(ADVISORY_RECORD, node_id="jackjack3")
    append_advisory_record(str(tmp_path), "log.jsonl", second)
    path = resolve_advisory_log_path(str(tmp_path), "log.jsonl")
    with open(path, encoding="utf-8") as fh:
        lines = [json.loads(line) for line in fh if line.strip()]
    assert lines == [ADVISORY_RECORD, second]


def test_append_refuses_record_without_authority_zero(tmp_path):
    bad = dict(ADVISORY_RECORD, authority="FULL")
    with pytest.raises(ValueError):
        append_advisory_record(str(tmp_path), "log.jsonl", bad)


def test_append_refuses_record_not_marked_non_authoritative(tmp_path):
    bad = dict(ADVISORY_RECORD)
    bad.pop("non_authoritative")
    with pytest.raises(ValueError):
        append_advisory_record(str(tmp_path), "log.jsonl", bad)
