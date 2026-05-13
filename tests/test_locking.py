"""Tests for file-lock coordination."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.maja_batch import _acquire_lock, _release_lock, LOCK_DIR


@pytest.fixture(autouse=True)
def clean_locks() -> None:
    lock_root = LOCK_DIR.resolve()
    lock_root.mkdir(parents=True, exist_ok=True)
    for child in lock_root.iterdir():
        if child.is_dir():
            child.rmdir()
        else:
            child.unlink()
    yield


def test_acquire_and_release() -> None:
    path = _acquire_lock("test_lock", timeout=5)
    assert path is not None
    assert path.is_dir()
    _release_lock(path)
    assert not path.exists()


def test_acquire_twice_fails() -> None:
    path1 = _acquire_lock("exclusive", timeout=5)
    assert path1 is not None
    path2 = _acquire_lock("exclusive", timeout=1)
    assert path2 is None
    _release_lock(path1)


def test_release_then_reacquire() -> None:
    """Verify lock can be released and re-acquired."""
    path1 = _acquire_lock("reacquire", timeout=5)
    assert path1 is not None
    _release_lock(path1)
    path2 = _acquire_lock("reacquire", timeout=5)
    assert path2 is not None
    _release_lock(path2)


def test_lock_isolation_different_names() -> None:
    """Different lock names should not conflict."""
    path_a = _acquire_lock("lock_a", timeout=5)
    path_b = _acquire_lock("lock_b", timeout=5)
    assert path_a is not None
    assert path_b is not None
    assert path_a != path_b
    _release_lock(path_a)
    _release_lock(path_b)


def test_lock_timeout_returns_none() -> None:
    path1 = _acquire_lock("timeout_lock", timeout=5)
    assert path1 is not None
    start = time.monotonic()
    path2 = _acquire_lock("timeout_lock", timeout=1)
    elapsed = time.monotonic() - start
    assert path2 is None
    assert elapsed < 2.0  # should return within ~1s
    _release_lock(path1)
