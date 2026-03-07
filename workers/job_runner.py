from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor

from api.models.job import JobStatus
from config.settings import Settings
from pipeline.context import PipelineContext
from pipeline.orchestrator import run_pipeline
from services.file_manager import FileManager
from services.job_store import JobStore

logger = logging.getLogger(__name__)


class WorkerPool:
    def __init__(self, settings: Settings, job_store: JobStore, file_manager: FileManager) -> None:
        self.settings = settings
        self.job_store = job_store
        self.file_manager = file_manager
        self._executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_jobs)

    def submit(self, job_id: str) -> None:
        self._executor.submit(self._run, job_id)

    def _run(self, job_id: str) -> None:
        record = self.job_store.get(job_id)
        if record is None:
            logger.error(f"Job {job_id} not found in store")
            return

        workspace = self.file_manager.create_workspace(job_id)
        ctx = PipelineContext(
            job_id=job_id,
            request=record.request,
            workspace=workspace,
            settings=self.settings,
            request_uploaded_file=record.uploaded_file,
        )

        try:
            run_pipeline(ctx, self.job_store)
        except Exception as e:
            logger.exception(f"Unhandled error in job {job_id}: {e}")
            self.job_store.update(job_id, status=JobStatus.FAILED, error=str(e))

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
