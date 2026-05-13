"""Tests for the multi-agent toolkit."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.agents.agentctl import ReviewAgent, DebugAgent, ProfileAgent, DocsCheckAgent


class TestReviewAgent:
    def test_gather_files(self) -> None:
        agent = ReviewAgent()
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            (td_path / "test.sh").write_text("#!/bin/bash\necho hi\n")
            (td_path / "test.py").write_text("print('hi')\n")
            (td_path / "readme.md").write_text("# Title\n")
            files = agent._gather_files([td])
            assert len(files) >= 3

    def test_check_shell_file(self) -> None:
        agent = ReviewAgent()
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            f = td_path / "bad.sh"
            f.write_text("echo hi\n")
            result = agent._check_file(f)
            assert result is not None
            items = [i.lower() for i in result["items"]]
            assert any("shebang" in i for i in items)


class TestDebugAgent:
    def test_no_log_dir(self) -> None:
        agent = DebugAgent()
        result = agent.run(logdir="/nonexistent_path_xyz")
        assert result["status"] == "no_logs"


class TestProfileAgent:
    def test_no_psutil(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("builtins.__import__", lambda name, *a, **kw: (_ for _ in ()).throw(ImportError) if name == "psutil" else __import__(name, *a, **kw))
        agent = ProfileAgent()
        result = agent.run()
        assert result["status"] == "unavailable"


class TestDocsCheckAgent:
    def test_empty_dir(self) -> None:
        agent = DocsCheckAgent()
        with tempfile.TemporaryDirectory() as td:
            result = agent.run(docsdir=td)
            assert result["total_md_files"] == 0

    def test_broken_link(self) -> None:
        agent = DocsCheckAgent()
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            md = td_path / "doc.md"
            md.write_text("[broken](nonexistent.png)\n", encoding="utf-8")
            result = agent.run(docsdir=td)
            assert result["total_md_files"] == 1
            assert len(result["broken_refs"]) >= 1 or len(result["missing_images"]) >= 1
