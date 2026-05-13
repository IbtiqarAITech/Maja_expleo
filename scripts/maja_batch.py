#!/usr/bin/env python3
"""
maja_batch.py — Multiprocessing batch runner for MAJA L2A processing.

Features:
  - ProcessPoolExecutor-based parallelism
  - YAML/JSON manifest input
  - --workers, --resume, --dry-run flags
  - Per-job logging + final summary report
  - File-lock coordination for safe parallel DTM/ENSO access

Usage:
  python scripts/maja_batch.py examples/manifest.yml --workers 4
  python scripts/maja_batch.py examples/manifest.json --dry-run
  python scripts/maja_batch.py examples/manifest.yml --resume
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

LOCK_DIR = Path("logs/locks")
STATE_DIR = Path("logs/state")
JOB_LOG_DIR = Path("logs/jobs")


def _acquire_lock(lock_name: str, timeout: float = 30.0) -> Optional[Path]:
    lock_root = LOCK_DIR.resolve()
    lock_dir = lock_root / f"{lock_name}.lockdir"
    lock_root.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.mkdir(str(lock_dir))
            return lock_dir
        except FileExistsError:
            time.sleep(0.5)
    return None


def _release_lock(lock_path: Optional[Path]) -> None:
    if lock_path and lock_path.is_dir():
        lock_path.rmdir()


def _load_state(manifest_name: str) -> Dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"{manifest_name}_state.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}


def _save_state(manifest_name: str, state: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"{manifest_name}_state.json"
    state_file.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def _run_job(job: Dict[str, Any], job_index: int) -> Dict[str, Any]:
    job_id = job.get("id", f"job_{job_index:04d}")
    JOB_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = JOB_LOG_DIR / f"{job_id}.log"
    start = time.monotonic()
    result: Dict[str, Any] = {
        "id": job_id,
        "index": job_index,
        "start": datetime.datetime.now().isoformat(),
        "command": job.get("command", ""),
        "returncode": -1,
        "duration_s": 0.0,
        "status": "unknown",
    }
    lock_name = job.get("lock")
    lock_path = None
    if lock_name:
        lock_path = _acquire_lock(lock_name)
        if lock_path is None:
            result["status"] = "skipped (lock timeout)"
            result["returncode"] = -2
            _append_log(log_file, result)
            return result
    try:
        cmd = job["command"]
        if isinstance(cmd, str):
            cmd = cmd.split()
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=job.get("timeout", 3600),
        )
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout[-2000:] if proc.stdout else ""
        result["stderr"] = proc.stderr[-2000:] if proc.stderr else ""
        result["status"] = "completed" if proc.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        result["status"] = "timed out"
        result["returncode"] = -3
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()
    finally:
        if lock_path:
            _release_lock(lock_path)
    result["duration_s"] = round(time.monotonic() - start, 2)
    _append_log(log_file, result)
    return result


def _append_log(log_file: Path, entry: Dict[str, Any]) -> None:
    ts = datetime.datetime.now().isoformat()
    line = f"[{ts}] job={entry['id']} status={entry['status']} rc={entry['returncode']} duration={entry['duration_s']}s\n"
    log_file.write_text(line, encoding="utf-8")


def load_manifest(path: str) -> Dict[str, Any]:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix in {".yaml", ".yml"}:
        if yaml is None:
            print("Warning: PyYAML not installed, trying JSON fallback.")
            return json.loads(raw)
        return yaml.safe_load(raw)
    return json.loads(raw)


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if "jobs" not in manifest or not isinstance(manifest["jobs"], list):
        errors.append("Missing 'jobs' list in manifest")
        return errors
    for i, job in enumerate(manifest["jobs"]):
        if "command" not in job:
            errors.append(f"jobs[{i}]: missing 'command'")
    return errors


def _generate_summary(
    manifest: Dict[str, Any], results: List[Dict[str, Any]], elapsed: float
) -> Dict[str, Any]:
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped (lock timeout)")
    timed_out = sum(1 for r in results if r["status"] == "timed out")
    errors = sum(1 for r in results if r["status"] == "error")
    total_duration = sum(r.get("duration_s", 0) for r in results)
    return {
        "manifest": str(manifest.get("name", "unknown")),
        "timestamp": datetime.datetime.now().isoformat(),
        "total_jobs": total,
        "completed": completed,
        "failed": failed,
        "skipped_locked": skipped,
        "timed_out": timed_out,
        "errors": errors,
        "wall_clock_s": round(elapsed, 2),
        "total_cpu_s": round(total_duration, 2),
        "success_rate": f"{completed / max(total, 1) * 100:.1f}%",
    }


def _save_summary(summary: Dict[str, Any], manifest_path: str) -> None:
    reports_dir = Path("reports/batch")
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(manifest_path).stem
    json_path = reports_dir / f"{stem}_{ts}.json"
    md_path = reports_dir / f"{stem}_{ts}.md"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    md_lines = [
        f"# Batch Summary: {summary['manifest']}",
        "",
        f"- **Timestamp**: {summary['timestamp']}",
        f"- **Total jobs**: {summary['total_jobs']}",
        f"- **Completed**: {summary['completed']}",
        f"- **Failed**: {summary['failed']}",
        f"- **Skipped (locked)**: {summary['skipped_locked']}",
        f"- **Timed out**: {summary['timed_out']}",
        f"- **Errors**: {summary['errors']}",
        f"- **Wall clock**: {summary['wall_clock_s']}s",
        f"- **Total CPU**: {summary['total_cpu_s']}s",
        f"- **Success rate**: {summary['success_rate']}",
        "",
        "## Job Details",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"  Summary report: {json_path}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MAJA multiprocessing batch runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("manifest", help="Path to manifest YAML/JSON file")
    parser.add_argument("--workers", type=int, default=2, help="Number of parallel workers (default: 2)")
    parser.add_argument("--resume", action="store_true", help="Skip previously completed jobs")
    parser.add_argument("--dry-run", action="store_true", help="Print jobs without executing")
    parser.add_argument("--timeout", type=int, default=3600, help="Per-job timeout in seconds (default: 3600)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    manifest_path = args.manifest
    if not os.path.isfile(manifest_path):
        print(f"Error: manifest not found: {manifest_path}")
        return 1
    manifest = load_manifest(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        for e in errors:
            print(f"  Validation error: {e}")
        return 1
    manifest_name = manifest.get("name", Path(manifest_path).stem)
    jobs = manifest["jobs"]
    print(f"Loaded manifest '{manifest_name}' with {len(jobs)} jobs")
    if args.dry_run:
        print("\n-- DRY RUN --")
        for i, job in enumerate(jobs):
            print(f"  [{i:04d}] {job.get('id', f'job_{i:04d}')}: {job.get('command', '(no command)')}")
        print(f"Would run with {args.workers} workers\n")
        return 0
    state = _load_state(manifest_name) if args.resume else {}
    completed_ids = set(state.get("completed", []))
    if completed_ids:
        print(f"Resume mode: {len(completed_ids)} jobs already completed, skipping")
    pending = [(i, j) for i, j in enumerate(jobs) if j.get("id", f"job_{i:04d}") not in completed_ids]
    if not pending:
        print("All jobs already completed. Nothing to do.")
        return 0
    print(f"Running {len(pending)}/{len(jobs)} jobs with {args.workers} workers...")
    new_results: List[Dict[str, Any]] = list(completed_ids)
    start_wall = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        fut_map = {executor.submit(_run_job, job, idx): (idx, job) for idx, job in pending}
        for fut in as_completed(fut_map):
            idx, job = fut_map[fut]
            try:
                result = fut.result()
                new_results.append(result)
                status_char = "[OK]" if result["status"] == "completed" else "[FAIL]"
                print(f"  {status_char} {result['id']}: {result['status']} ({result['duration_s']}s)")
            except Exception as exc:
                print(f"  [FAIL] job_{idx:04d}: unexpected error: {exc}")
                new_results.append({"id": f"job_{idx:04d}", "status": "error", "error": str(exc)})
    elapsed = time.monotonic() - start_wall
    completed_set = set(
        r["id"] for r in new_results if isinstance(r, dict) and r.get("status") == "completed"
    )
    _save_state(manifest_name, {"completed": list(completed_set)})
    summary = _generate_summary(manifest, [r for r in new_results if isinstance(r, dict)], elapsed)
    _save_summary(summary, manifest_path)
    return 0 if summary["failed"] == 0 and summary["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
