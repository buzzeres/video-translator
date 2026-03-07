from __future__ import annotations
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from api.models.job import JobRecord, JobRequest

router = APIRouter()

ALLOWED_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


@router.post("/upload", status_code=202)
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    target_language: str = Form("Spanish"),
    generate_subtitles: bool = Form(True),
    ai_dubbing: bool = Form(True),
    voice_matching: bool = Form(False),
    lip_sync: bool = Form(False),
    keep_original_audio: bool = Form(False),
) -> JobRecord:
    settings = request.app.state.settings
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTS)}")

    # Save upload to temp location
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / (file.filename or f"upload{ext}")
    with open(tmp_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    job_req = JobRequest(
        target_language=target_language,
        generate_subtitles=generate_subtitles,
        ai_dubbing=ai_dubbing,
        voice_matching=voice_matching,
        lip_sync=lip_sync,
        keep_original_audio=keep_original_audio,
    )
    record = request.app.state.job_store.create(job_req, uploaded_file=str(tmp_path))
    request.app.state.worker_pool.submit(record.job_id)
    return record
