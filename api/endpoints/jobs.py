from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from api.models.job import JobRequest, JobRecord, JobStatus

router = APIRouter()


def _store(request: Request):
    return request.app.state.job_store


def _pool(request: Request):
    return request.app.state.worker_pool


@router.post("/jobs", status_code=202)
async def create_job(job_req: JobRequest, request: Request) -> JobRecord:
    if not job_req.video_url:
        raise HTTPException(400, "video_url is required. For file upload use POST /upload")
    record = _store(request).create(job_req)
    _pool(request).submit(record.job_id)
    return record


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request) -> JobRecord:
    record = _store(request).get(job_id)
    if not record:
        raise HTTPException(404, f"Job {job_id} not found")
    return record


@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str, request: Request):
    record = _store(request).get(job_id)
    if not record:
        raise HTTPException(404, f"Job {job_id} not found")
    return {
        "job_id": job_id,
        "status": record.status,
        "progress": record.progress,
        "current_step": record.current_step,
        "error": record.error,
    }


@router.get("/jobs")
async def list_jobs(request: Request):
    return _store(request).list_all()


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str, request: Request):
    store = _store(request)
    record = store.get(job_id)
    if not record:
        raise HTTPException(404, f"Job {job_id} not found")
    request.app.state.file_manager.cleanup(job_id)
    store.delete(job_id)


@router.get("/languages")
async def get_languages():
    from config.languages import LANGUAGE_NAMES
    return LANGUAGE_NAMES
