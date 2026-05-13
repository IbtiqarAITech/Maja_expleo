"""Tests for cache/resume state persistence."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.maja_batch import _load_state, _save_state, STATE_DIR


@pytest.fixture(autouse=True)
def clean_state() -> None:
    if STATE_DIR.exists():
        for f in STATE_DIR.iterdir():
            f.unlink()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    yield


def test_save_and_load_state() -> None:
    _save_state("test_manifest", {"completed": ["job1", "job2"]})
    state = _load_state("test_manifest")
    assert state["completed"] == ["job1", "job2"]


def test_load_missing_state() -> None:
    state = _load_state("nonexistent")
    assert state == {}


def test_overwrite_state() -> None:
    _save_state("overwrite_test", {"completed": ["job1"]})
    _save_state("overwrite_test", {"completed": ["job1", "job2"]})
    state = _load_state("overwrite_test")
    assert len(state["completed"]) == 2


def test_state_file_valid_json(tmp_path: Path) -> None:
    _save_state("valid_json_test", {"key": "value"})
    state_file = STATE_DIR / "valid_json_test_state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["key"] == "value"
