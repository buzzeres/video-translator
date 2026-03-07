from __future__ import annotations
import json
import subprocess
from pathlib import Path

import ffmpeg

from pipeline.context import PipelineContext


def run(ctx: PipelineContext) -> None:
    audio_dir = ctx.workspace / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_out = audio_dir / "extracted.wav"

    # Extract 16kHz mono WAV for Whisper
    (
        ffmpeg
        .input(str(ctx.video_path))
        .audio
        .output(str(audio_out), ac=1, ar=16000, acodec="pcm_s16le")
        .overwrite_output()
        .run(quiet=True)
    )
    ctx.audio_path = audio_out
    ctx.video_metadata = _get_metadata(ctx.video_path)


def _get_metadata(video_path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
        )
        fps_str = video_stream.get("r_frame_rate", "25/1")
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) else 25.0
        duration = float(data.get("format", {}).get("duration", 0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        return {"fps": fps, "duration": duration, "width": width, "height": height}
    except Exception:
        return {"fps": 25.0, "duration": 0.0, "width": 0, "height": 0}
