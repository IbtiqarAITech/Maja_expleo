#!/usr/bin/env python3
"""
agentctl.py — Multi-Agent Developer Toolkit for MAJA.

Agents:
  review     — Static code review of shell & Python files
  debug      — Anomaly detection in MAJA logs and outputs
  profile    — Resource usage profiling (CPU, memory, disk)
  docscheck  — Validate documentation references and links

Usage:
  python -m tools.agents.agentctl review [--paths ...]
  python -m tools.agents.agentctl debug   [--logdir ...]
  python -m tools.agents.agentctl profile [--pid ...]
  python -m tools.agents.agentctl docscheck [--docsdir ...]
  python -m tools.agents.agentctl all

Output:
  JSON + Markdown reports under reports/<agent>/<timestamp>/
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

REPORTS_DIR = Path(os.environ.get("MAJA_AGENT_REPORT_DIR", "reports"))


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _report_dir(agent_name: str) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return _ensure_dir(REPORTS_DIR / agent_name / ts)


def _write_report(report_dir: Path, data: Dict[str, Any]) -> None:
    report_dir.joinpath("report.json").write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8"
    )
    md = _json_to_markdown(data)
    report_dir.joinpath("report.md").write_text(md, encoding="utf-8")
    print(f"  Report written to {report_dir}")


def _json_to_markdown(data: Dict[str, Any], level: int = 1) -> str:
    lines: List[str] = []
    prefix = "#" * level
    for key, val in data.items():
        if isinstance(val, dict):
            lines.append(f"\n{prefix} {key.replace('_', ' ').title()}\n")
            lines.append(_json_to_markdown(val, level + 1))
        elif isinstance(val, list):
            lines.append(f"\n{prefix} {key.replace('_', ' ').title()}\n")
            for item in val:
                if isinstance(item, dict):
                    lines.append(_json_to_markdown(item, level + 2))
                else:
                    lines.append(f"- {item}\n")
        else:
            lines.append(f"- **{key}**: {val}\n")
    return "".join(lines)


# ── Agents ─────────────────────────────────────────────────────────────────


class ReviewAgent:
    """Static analysis of shell and Python files."""

    def run(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        scan_paths = paths or ["."]
        files = self._gather_files(scan_paths)
        results: Dict[str, Any] = {
            "agent": "review",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_files": len(files),
            "issues": [],
            "summary": {},
        }
        with ThreadPoolExecutor(max_workers=4) as pool:
            checks = list(pool.map(self._check_file, files))
        issues = [c for c in checks if c]
        results["issues"] = issues
        results["summary"] = {
            "files_with_issues": len(issues),
            "total_issues": sum(i.get("count", 1) for i in issues),
        }
        return results

    def _gather_files(self, paths: List[str]) -> List[Path]:
        exts = {".sh", ".py", ".md", ".txt", ".yml", ".yaml", ".cfg", ".ini"}
        files: List[Path] = []
        for p in paths:
            root = Path(p)
            if root.is_file() and root.suffix in exts:
                files.append(root)
            elif root.is_dir():
                for f in root.rglob("*"):
                    if f.is_file() and f.suffix in exts and ".git" not in f.parts:
                        files.append(f)
        return sorted(files)

    def _check_file(self, path: Path) -> Optional[Dict[str, Any]]:
        issues: List[str] = []
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
        if path.suffix == ".sh":
            if not text.startswith("#!/"):
                issues.append("Missing shebang")
            if "\r\n" in text:
                issues.append("CRLF line endings (use LF)")
            if not text.strip().endswith("\n"):
                issues.append("Missing trailing newline")
        elif path.suffix == ".py":
            if "\r\n" in text:
                issues.append("CRLF line endings (use LF)")
            if not text.strip().endswith("\n"):
                issues.append("Missing trailing newline")
        elif path.suffix in {".md"}:
            for i, line in enumerate(text.splitlines(), 1):
                if "TODO" in line:
                    issues.append(f"Line {i}: Contains TODO marker")
        if issues:
            return {"path": str(path), "count": len(issues), "items": issues}
        return None


class DebugAgent:
    """Scan MAJA logs for errors, warnings, and anomalies."""

    LOG_PATTERNS = {
        "error": re.compile(r"(?i)\b(error|exception|traceback|failed|failure)\b"),
        "warning": re.compile(r"(?i)\b(warning|warn)\b"),
        "oom": re.compile(r"(?i)\b(out of memory|killed|oom.killer|cannot allocate)\b"),
        "disk": re.compile(r"(?i)\b(disk full|no space left|i/o error)\b"),
    }

    def run(self, logdir: Optional[str] = None) -> Dict[str, Any]:
        search_dir = Path(logdir) if logdir else Path("logs")
        if not search_dir.exists():
            return {
                "agent": "debug",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "no_logs",
                "message": f"Log directory not found: {search_dir}",
            }
        log_files = sorted(search_dir.rglob("*"))
        log_files = [f for f in log_files if f.is_file() and f.stat().st_size > 0]
        results: Dict[str, Any] = {
            "agent": "debug",
            "timestamp": datetime.datetime.now().isoformat(),
            "log_dir": str(search_dir),
            "total_log_files": len(log_files),
            "matches": [],
        }
        for lf in log_files:
            try:
                text = lf.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            file_matches: Dict[str, List[str]] = {}
            for category, pattern in self.LOG_PATTERNS.items():
                found = pattern.findall(text)
                if found:
                    file_matches[category] = list(set(found))
            if file_matches:
                results["matches"].append(
                    {"file": str(lf), "size_bytes": lf.stat().st_size, "categories": file_matches}
                )
        results["total_matches"] = len(results["matches"])
        return results


class ProfileAgent:
    """Resource usage profiling via psutil."""

    def run(self, pid: Optional[int] = None, duration: int = 5) -> Dict[str, Any]:
        try:
            import psutil
        except ImportError:
            return {
                "agent": "profile",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "unavailable",
                "message": "psutil not installed. Run: pip install psutil",
            }
        results: Dict[str, Any] = {
            "agent": "profile",
            "timestamp": datetime.datetime.now().isoformat(),
            "system": {},
            "processes": [],
        }
        results["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "memory": dict(psutil.virtual_memory()._asdict()),
            "disk": dict(psutil.disk_usage("/")._asdict()),
        }
        targets = [psutil.Process(pid)] if pid else [psutil.Process(p.info["pid"]) for p in psutil.process_iter(["pid", "name"]) if "maja" in p.info["name"].lower()]
        for proc in targets[:10]:
            try:
                with proc.oneshot():
                    info = {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "cpu_percent": proc.cpu_percent(interval=0.1),
                        "memory_rss": proc.memory_info().rss,
                        "status": proc.status(),
                    }
                    results["processes"].append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return results


class DocsCheckAgent:
    """Validate documentation file references and links."""

    LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def run(self, docsdir: Optional[str] = None) -> Dict[str, Any]:
        search_dir = Path(docsdir) if docsdir else Path("docs")
        if not search_dir.exists():
            search_dir = Path(".")
        md_files = sorted(search_dir.rglob("*.md")) if search_dir.is_dir() else [search_dir]
        results: Dict[str, Any] = {
            "agent": "docscheck",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_md_files": len(md_files),
            "broken_refs": [],
            "missing_images": [],
        }
        for mf in md_files:
            try:
                text = mf.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            base = mf.parent
            for link_text, link_target in self.LINK_RE.findall(text):
                if link_target.startswith(("http://", "https://", "ftp://")):
                    continue
                if link_target.startswith("#"):
                    continue
                resolved = (base / link_target).resolve()
                if not resolved.exists():
                    results["broken_refs"].append(
                        {"file": str(mf), "link": link_target, "resolved": str(resolved)}
                    )
            for img_tag in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', text):
                img_src = img_tag.group(2)
                if img_src.startswith(("http://", "https://")):
                    continue
                resolved = (base / img_src).resolve()
                if not resolved.exists():
                    results["missing_images"].append(
                        {"file": str(mf), "image": img_src, "resolved": str(resolved)}
                    )
        return results


# ── CLI ────────────────────────────────────────────────────────────────────


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MAJA Multi-Agent Developer Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--format", default="both", choices=["json", "md", "both"])
    parser.add_argument("--target", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true")
    sub = parser.add_subparsers(dest="agent", required=True)

    p_review = sub.add_parser("review", help="Static code review")
    p_review.add_argument("--paths", nargs="*", default=None, help="Files/dirs to scan")

    p_debug = sub.add_parser("debug", help="Log anomaly detection")
    p_debug.add_argument("--logdir", default=None, help="Log directory to scan")

    p_profile = sub.add_parser("profile", help="Resource profiling")
    p_profile.add_argument("--pid", type=int, default=None, help="Specific PID")
    p_profile.add_argument("--duration", type=int, default=5, help="Sampling duration (s)")

    p_docs = sub.add_parser("docscheck", help="Documentation validation")
    p_docs.add_argument("--docsdir", default=None, help="Docs root directory")

    sub.add_parser("all", help="Run all agents sequentially")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    global REPORTS_DIR
    if args.output_dir:
        REPORTS_DIR = Path(args.output_dir)
    agents = {
        "review": ReviewAgent(),
        "debug": DebugAgent(),
        "profile": ProfileAgent(),
        "docscheck": DocsCheckAgent(),
    }
    if args.agent == "all":
        for name, agent_instance in agents.items():
            print(f"\n── Running agent: {name} ──")
            try:
                data = agent_instance.run()
            except Exception as e:
                data = {"agent": name, "error": str(e)}
            _write_report(_report_dir(name), data)
        print("\nAll agents complete.")
        return 0

    instance = agents.get(args.agent)
    if not instance:
        print(f"Unknown agent: {args.agent}")
        return 1

    kwargs = {}
    if args.agent == "review":
        kwargs["paths"] = args.paths
    elif args.agent == "debug":
        kwargs["logdir"] = args.logdir
    elif args.agent == "profile":
        kwargs["pid"] = args.pid
        kwargs["duration"] = args.duration
    elif args.agent == "docscheck":
        kwargs["docsdir"] = args.docsdir

    print(f"Running agent: {args.agent}")
    data = instance.run(**kwargs)
    _write_report(_report_dir(args.agent), data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
