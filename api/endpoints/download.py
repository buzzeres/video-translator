from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

router = APIRouter()

ARTIFACT_NAMES = {
    "video": ("final.mp4", "video/mp4"),
    "subtitles_srt": ("subtitles.srt", "text/plain"),
    "subtitles_vtt": ("subtitles.vtt", "text/vtt"),
}


@router.get("/download/{job_id}/{artifact}")
async def download_artifact(job_id: str, artifact: str, request: Request):
    if artifact not in ARTIFACT_NAMES:
        raise HTTPException(400, f"Unknown artifact '{artifact}'. Choose from: {', '.join(ARTIFACT_NAMES)}")

    record = request.app.state.job_store.get(job_id)
    if not record:
        raise HTTPException(404, "Job not found")
    if artifact not in record.artifacts:
        raise HTTPException(404, f"Artifact '{artifact}' not ready yet")

    file_path = Path(record.artifacts[artifact])
    if not file_path.exists():
        raise HTTPException(404, "File not found on disk")

    filename, media_type = ARTIFACT_NAMES[artifact]
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
