from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

router = APIRouter()
CHUNK = 1024 * 1024  # 1 MB


@router.get("/stream/{job_id}")
async def stream_video(job_id: str, request: Request):
    record = request.app.state.job_store.get(job_id)
    if not record:
        raise HTTPException(404, "Job not found")
    artifacts = record.artifacts
    if "video" not in artifacts:
        raise HTTPException(404, "Video not ready yet")

    video_path = Path(artifacts["video"])
    if not video_path.exists():
        raise HTTPException(404, "Video file missing")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        start, end = _parse_range(range_header, file_size)
        length = end - start + 1

        def iter_file():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(CHUNK, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
            },
        )

    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )


def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
    try:
        unit, ranges = range_header.split("=")
        start_str, end_str = ranges.split("-")
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        end = min(end, file_size - 1)
        return start, end
    except Exception:
        return 0, file_size - 1
