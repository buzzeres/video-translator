from __future__ import annotations
import shutil
from pathlib import Path

from pipeline.context import PipelineContext, StepSkippedException


def run(ctx: PipelineContext) -> None:
    if ctx.request.video_url:
        _download_url(ctx)
    elif ctx.request_uploaded_file:
        _copy_uploaded(ctx)
    else:
        raise ValueError("No video_url and no uploaded file provided.")


def _download_url(ctx: PipelineContext) -> None:
    import yt_dlp

    input_dir = ctx.workspace / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "outtmpl": str(input_dir / "%(title).80s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(ctx.request.video_url, download=True)
        filename = ydl.prepare_filename(info)
        # yt-dlp may change extension after merging
        path = Path(filename)
        if not path.exists():
            path = path.with_suffix(".mp4")
        ctx.video_path = path


def _copy_uploaded(ctx: PipelineContext) -> None:
    src = Path(ctx.request_uploaded_file)
    dest = ctx.workspace / "input" / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    ctx.video_path = dest
