"""Tests for manifest parsing and validation."""

import json
import os
import tempfile
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.maja_batch import load_manifest, validate_manifest


SAMPLE_MANIFEST = {
    "name": "test-batch",
    "version": "1.0",
    "jobs": [
        {"id": "job1", "command": "echo hello", "lock": "test", "timeout": 60},
        {"id": "job2", "command": "echo world"},
    ],
}


@pytest.fixture
def json_manifest(tmp_path: Path) -> str:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(SAMPLE_MANIFEST), encoding="utf-8")
    return str(path)


@pytest.fixture
def yaml_manifest(tmp_path: Path) -> str:
    path = tmp_path / "manifest.yml"
    path.write_text(
        "name: test-batch\nversion: '1.0'\njobs:\n  - id: job1\n    command: echo hello\n    lock: test\n    timeout: 60\n  - id: job2\n    command: echo world\n",
        encoding="utf-8",
    )
    return str(path)


def test_load_json_manifest(json_manifest: str) -> None:
    data = load_manifest(json_manifest)
    assert data["name"] == "test-batch"
    assert len(data["jobs"]) == 2


def test_load_yaml_manifest(yaml_manifest: str) -> None:
    data = load_manifest(yaml_manifest)
    assert data["name"] == "test-batch"
    assert len(data["jobs"]) == 2


def test_validate_valid_manifest() -> None:
    errors = validate_manifest(SAMPLE_MANIFEST)
    assert errors == []


def test_validate_missing_jobs() -> None:
    errors = validate_manifest({"name": "bad"})
    assert "Missing 'jobs' list" in errors[0]


def test_validate_missing_command() -> None:
    errors = validate_manifest({"jobs": [{"id": "x"}]})
    assert any("missing 'command'" in e for e in errors)


def test_manifest_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest("/nonexistent/manifest.json")
