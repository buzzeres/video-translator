from __future__ import annotations
import logging
from pipeline.context import PipelineContext, StepSkippedException

logger = logging.getLogger(__name__)


def _fmt_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_vtt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def run(ctx: PipelineContext) -> None:
    if not ctx.request.generate_subtitles:
        raise StepSkippedException("generate_subtitles disabled")

    segments = ctx.translated_segments or ctx.segments or []
    sub_dir = ctx.workspace / "subtitles"
    sub_dir.mkdir(parents=True, exist_ok=True)

    srt_path = sub_dir / "subtitles.srt"
    vtt_path = sub_dir / "subtitles.vtt"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            text = seg.get("translated_text") or seg.get("text", "")
            f.write(f"{i}\n")
            f.write(f"{_fmt_srt(seg['start'])} --> {_fmt_srt(seg['end'])}\n")
            f.write(f"{text}\n\n")

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            text = seg.get("translated_text") or seg.get("text", "")
            f.write(f"{_fmt_vtt(seg['start'])} --> {_fmt_vtt(seg['end'])}\n")
            f.write(f"{text}\n\n")

    ctx.subtitle_srt_path = srt_path
    ctx.subtitle_vtt_path = vtt_path
    logger.info(f"Subtitles written: {srt_path}, {vtt_path}")
