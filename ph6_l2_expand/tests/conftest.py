import json
from pathlib import Path

import pytest

# ph6_l2_expand/tests/conftest.py -> parents[0]=tests, [1]=ph6_l2_expand, [2]=repo root
L2_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
PH6_DIR = REPO_ROOT / "ph6"

SAMPLE_OBJECT_ID = "internal_000001"

SAMPLE_SOURCE_OBJECT = {
    "object_id": SAMPLE_OBJECT_ID,
    "motion_fraction": 0.42,
    "rssi_event": "stable",
    "continuity_chain": "c01",
}


@pytest.fixture
def sample_source_object():
    return dict(SAMPLE_SOURCE_OBJECT)


@pytest.fixture
def source_object_path(tmp_path):
    p = tmp_path / "source_object.json"
    p.write_text(json.dumps(SAMPLE_SOURCE_OBJECT), encoding="utf-8")
    return p


@pytest.fixture
def mram_s_dir(tmp_path):
    d = tmp_path / "mram-s"
    d.mkdir()
    return d


def iter_l2_source_files():
    for path in sorted(L2_DIR.rglob("*.py")):
        if "tests" in path.relative_to(L2_DIR).parts:
            continue
        if "__pycache__" in path.parts:
            continue
        yield path
