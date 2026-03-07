from __future__ import annotations
import logging
from pathlib import Path

import ffmpeg

from pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    source_video = ctx.lipsynced_video_path or ctx.video_path
    output_dir = ctx.workspace / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    final_out = output_dir / "final.mp4"

    use_dubbed = ctx.request.ai_dubbing and ctx.dubbed_audio_path and ctx.dubbed_audio_path.exists()
    burn_subs = ctx.request.generate_subtitles and ctx.subtitle_srt_path and ctx.subtitle_srt_path.exists()

    if use_dubbed and ctx.request.keep_original_audio:
        _render_mixed_audio(source_video, ctx.dubbed_audio_path, ctx.audio_path,
                            ctx.subtitle_srt_path if burn_subs else None, final_out)
    elif use_dubbed:
        _render_replaced_audio(source_video, ctx.dubbed_audio_path,
                               ctx.subtitle_srt_path if burn_subs else None, final_out)
    elif burn_subs:
        _render_subs_only(source_video, ctx.subtitle_srt_path, final_out)
    else:
        _render_passthrough(source_video, final_out)

    ctx.final_video_path = final_out
    logger.info(f"Final video rendered: {final_out}")


def _render_replaced_audio(video: Path, audio: Path, srt: Path | None, out: Path) -> None:
    v = ffmpeg.input(str(video))
    a = ffmpeg.input(str(audio))
    video_stream = v.video
    if srt:
        srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
        video_stream = video_stream.filter("subtitles", srt_escaped)
    (
        ffmpeg
        .output(video_stream, a.audio, str(out),
                vcodec="libx264", acodec="aac",
                crf=23, preset="fast",
                **{"map_metadata": "-1"})
        .overwrite_output()
        .run(quiet=True)
    )


def _render_mixed_audio(video: Path, dubbed: Path, original: Path, srt: Path | None, out: Path) -> None:
    v = ffmpeg.input(str(video))
    a_dubbed = ffmpeg.input(str(dubbed))
    a_orig = ffmpeg.input(str(original))
    video_stream = v.video
    if srt:
        srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
        video_stream = video_stream.filter("subtitles", srt_escaped)
    mixed = ffmpeg.filter([a_dubbed.audio, a_orig.audio], "amix",
                          inputs=2, duration="longest",
                          weights="1 0.15")
    (
        ffmpeg
        .output(video_stream, mixed, str(out),
                vcodec="libx264", acodec="aac",
                crf=23, preset="fast")
        .overwrite_output()
        .run(quiet=True)
    )


def _render_subs_only(video: Path, srt: Path, out: Path) -> None:
    srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
    v = ffmpeg.input(str(video))
    video_stream = v.video.filter("subtitles", srt_escaped)
    (
        ffmpeg
        .output(video_stream, v.audio, str(out),
                vcodec="libx264", acodec="aac",
                crf=23, preset="fast")
        .overwrite_output()
        .run(quiet=True)
    )


def _render_passthrough(video: Path, out: Path) -> None:
    (
        ffmpeg
        .input(str(video))
        .output(str(out), vcodec="copy", acodec="copy")
        .overwrite_output()
        .run(quiet=True)
    )
