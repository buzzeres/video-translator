from __future__ import annotations
import logging
import subprocess
from pipeline.context import PipelineContext, StepSkippedException

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    if not ctx.request.lip_sync:
        raise StepSkippedException("lip_sync disabled")
    if not ctx.settings.wav2lip_enabled:
        raise StepSkippedException("WAV2LIP_ENABLED=false in settings")

    checkpoint = ctx.settings.wav2lip_checkpoint_path
    if not checkpoint.exists():
        logger.warning(
            f"Wav2Lip checkpoint not found at {checkpoint}. "
            "Skipping lip-sync. See README for Wav2Lip setup instructions."
        )
        raise StepSkippedException(f"Wav2Lip checkpoint not found: {checkpoint}")

    audio_source = ctx.dubbed_audio_path or ctx.audio_path
    output_path = ctx.workspace / "lipsync" / "output.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ctx.settings.wav2lip_python_path,
        "Wav2Lip/inference.py",
        "--checkpoint_path", str(checkpoint),
        "--face", str(ctx.video_path),
        "--audio", str(audio_source),
        "--outfile", str(output_path),
        "--nosmooth",
    ]

    logger.info(f"Running Wav2Lip: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed (exit {result.returncode}): {result.stderr[-500:]}")

    ctx.lipsynced_video_path = output_path
    logger.info(f"Lip-sync complete: {output_path}")
