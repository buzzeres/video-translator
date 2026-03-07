from __future__ import annotations
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from api.models.job import JobRecord, JobRequest, JobStatus, STATUS_LABELS


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.RLock()

    def create(self, request: JobRequest, uploaded_file: Optional[str] = None) -> JobRecord:
        job_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        record = JobRecord(
            job_id=job_id,
            request=request,
            created_at=now,
            updated_at=now,
            uploaded_file=uploaded_file,
        )
        with self._lock:
            self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> Optional[JobRecord]:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            data = record.model_dump()
            data.update(kwargs)
            data["updated_at"] = datetime.now(timezone.utc)
            if "status" in kwargs:
                status = kwargs["status"]
                if "current_step" not in kwargs:
                    data["current_step"] = STATUS_LABELS.get(status, str(status))
            updated = JobRecord(**data)
            self._jobs[job_id] = updated
            return updated

    def list_all(self) -> list[JobRecord]:
        with self._lock:
            return list(self._jobs.values())

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None
