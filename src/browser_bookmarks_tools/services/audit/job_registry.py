"""In-memory registry of running/finished audit jobs.

Same convention as activity_log.py's ring buffer: a module-level dict guarded
by a plain lock, no persistence for the job record itself (ephemeral - a
restart mid-scan loses the live counter, but LinkAuditStore rows already
written survive). Deliberately not a job queue: this process only ever runs
one audit job's worker loop at a time per job_id via asyncio.create_task.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

JobStatus = Literal["running", "done", "cancelled", "error"]

_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def create_job(*, browser: str, profile_name: str | None, total: int) -> str:
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "browser": browser,
            "profile_name": profile_name,
            "status": "running",
            "total": total,
            "checked": 0,
            "counts_by_status": {},
            "cancelled": False,
            "error": None,
            "started_at": _now_iso(),
            "finished_at": None,
        }
    return job_id


def update_progress(job_id: str, *, checked_delta: int, status_counts_delta: dict[str, int]) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["checked"] += checked_delta
        for status, delta in status_counts_delta.items():
            job["counts_by_status"][status] = job["counts_by_status"].get(status, 0) + delta


def finish_job(job_id: str, *, status: JobStatus = "done", error: str | None = None) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["status"] = status
        job["error"] = error
        job["finished_at"] = _now_iso()


def request_cancel(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        if not job or job["status"] != "running":
            return False
        job["cancelled"] = True
        return True


def is_cancelled(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        return bool(job and job["cancelled"])


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None
