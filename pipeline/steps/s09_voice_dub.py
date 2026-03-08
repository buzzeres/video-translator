from __future__ import annotations
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pipeline.context import PipelineContext, StepSkippedException
from pipeline.steps.s04_diarize import get_speaker_for_segment
from services.tts_service import TTSService

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    if not ctx.request.ai_dubbing:
        raise StepSkippedException("ai_dubbing disabled")

    tts = TTSService(ctx.settings)
    tts_dir = ctx.workspace / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)

    segments = ctx.translated_segments or []
    # Each entry: (start_seconds, audio_path)
    tts_files: list[tuple[float, Path]] = []
    speaker_samples: dict[str, Optional[Path]] = {}

    for seg in segments:
        seg_id = seg["id"]
        # Pass a .wav hint; synthesize() may change extension (e.g. to .mp3)
        out_hint = tts_dir / f"seg_{seg_id:04d}.wav"
        text = seg.get("translated_text", seg.get("text", ""))
        if not text.strip():
            continue

        speaker_id = get_speaker_for_segment(seg, ctx.diarization or {})

        try:
            if ctx.request.voice_matching:
                if speaker_id not in speaker_samples:
                    speaker_samples[speaker_id] = _extract_speaker_sample(
                        ctx.audio_path, ctx.diarization, speaker_id, ctx.workspace
                    )
                sample = speaker_samples[speaker_id]
                actual_path = tts.synthesize_cloned(
                    text, ctx.request.target_language, sample, out_hint
                )
            else:
                actual_path = tts.synthesize(
                    text, ctx.request.target_language, out_hint
                )
        except Exception as e:
            logger.warning(f"TTS failed for segment {seg_id}: {e}")
            continue

        if actual_path and actual_path.exists():
            tts_files.append((seg["start"], actual_path))
            logger.debug(f"Synthesized segment {seg_id} → {actual_path.name}")

    if not tts_files:
        logger.warning("No TTS segments were produced — skipping dubbing.")
        raise StepSkippedException("No TTS audio produced")

    logger.info(f"Mixing {len(tts_files)} dubbed segments via ffmpeg...")
    dubbed_path = ctx.workspace / "audio" / "dubbed.wav"
    _mix_with_ffmpeg(tts_files, ctx.video_metadata.get("duration", 0.0), dubbed_path)

    if dubbed_path.exists():
        ctx.dubbed_audio_path = dubbed_path
        logger.info(f"Dubbed audio ready: {dubbed_path}")
    else:
        logger.error("ffmpeg mix produced no output — falling back to first segment")
        if tts_files:
            shutil.copy2(str(tts_files[0][1]), str(dubbed_path))
            ctx.dubbed_audio_path = dubbed_path


def _mix_with_ffmpeg(tts_files: list[tuple[float, Path]], total_dur: float, out_path: Path) -> None:
    """Use ffmpeg adelay+amix to position each audio clip at its original timestamp."""
    inputs = []
    filter_parts = []

    for i, (start_t, audio_path) in enumerate(tts_files):
        inputs += ["-i", str(audio_path)]
        delay_ms = int(start_t * 1000)
        filter_parts.append(f"[{i}]adelay={delay_ms}|{delay_ms}[d{i}]")

    n = len(tts_files)
    mix_inputs = "".join(f"[d{i}]" for i in range(n))
    filter_parts.append(f"{mix_inputs}amix=inputs={n}:duration=longest:normalize=0[out]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "2",
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mix failed: {result.stderr[-500:]}")


def _extract_speaker_sample(
    audio_path: Optional[Path],
    diarization: Optional[dict],
    speaker_id: str,
    workspace: Path,
) -> Optional[Path]:
    if not audio_path or not diarization:
        return None
    ranges = diarization.get(speaker_id, [])
    for start, end in ranges:
        if end - start >= 3.0:
            sample_path = workspace / "audio" / f"sample_{speaker_id}.wav"
            duration = min(end - start, 10.0)
            try:
                import ffmpeg
                (
                    ffmpeg
                    .input(str(audio_path), ss=start, t=duration)
                    .output(str(sample_path), ac=1, ar=16000)
                    .overwrite_output()
                    .run(quiet=True)
                )
                return sample_path
            except Exception:
                return None
    return None
