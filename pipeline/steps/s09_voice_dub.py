from __future__ import annotations
import logging
import shutil
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
    tts_files: list[tuple[float, Path]] = []
    speaker_samples: dict[str, Optional[Path]] = {}

    for seg in segments:
        seg_id = seg["id"]
        out_path = tts_dir / f"seg_{seg_id:04d}.wav"
        text = seg.get("translated_text", seg.get("text", ""))
        if not text.strip():
            continue

        speaker_id = get_speaker_for_segment(seg, ctx.diarization or {})

        if ctx.request.voice_matching:
            if speaker_id not in speaker_samples:
                speaker_samples[speaker_id] = _extract_speaker_sample(
                    ctx.audio_path, ctx.diarization, speaker_id, ctx.workspace
                )
            sample = speaker_samples[speaker_id]
            try:
                tts.synthesize_cloned(text, ctx.request.target_language, sample, out_path)
            except Exception as e:
                logger.warning(f"Voice cloning failed for seg {seg_id}: {e}. Falling back.")
                tts.synthesize(text, ctx.request.target_language, out_path)
        else:
            tts.synthesize(text, ctx.request.target_language, out_path)

        if out_path.exists():
            original_dur = seg["end"] - seg["start"]
            stretched_path = tts_dir / f"seg_{seg_id:04d}_s.wav"
            final_wav = _stretch_to_duration(out_path, original_dur, stretched_path)
            tts_files.append((seg["start"], final_wav))
            logger.info(f"Synthesized segment {seg_id}")

    dubbed_path = ctx.workspace / "audio" / "dubbed.wav"
    _mix_to_timeline(tts_files, ctx.video_metadata.get("duration", 0.0), dubbed_path)
    ctx.dubbed_audio_path = dubbed_path
    logger.info(f"Dubbed audio written to {dubbed_path}")


def _extract_speaker_sample(
    audio_path: Optional[Path],
    diarization: Optional[dict],
    speaker_id: str,
    workspace: Path,
) -> Optional[Path]:
    if not audio_path or not diarization:
        return None
    ranges = diarization.get(speaker_id, [])
    if not ranges:
        return None
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


def _stretch_to_duration(wav_path: Path, target_dur: float, out_path: Path) -> Path:
    try:
        import librosa
        import soundfile as sf
        y, sr = librosa.load(str(wav_path), sr=None)
        current_dur = len(y) / sr
        if current_dur <= 0 or target_dur <= 0:
            return wav_path
        rate = current_dur / target_dur
        rate = max(0.5, min(rate, 2.0))
        if abs(rate - 1.0) < 0.05:
            return wav_path
        stretched = librosa.effects.time_stretch(y, rate=rate)
        sf.write(str(out_path), stretched, sr)
        return out_path
    except Exception:
        return wav_path


def _mix_to_timeline(tts_files: list[tuple[float, Path]], total_dur: float, out_path: Path) -> None:
    try:
        import numpy as np
        import soundfile as sf

        if not tts_files:
            sr = 22050
            silence = np.zeros(int(max(total_dur, 1) * sr), dtype=np.float32)
            sf.write(str(out_path), silence, sr)
            return

        first_y, sr = sf.read(str(tts_files[0][1]), dtype="float32")
        total_samples = max(int(total_dur * sr), 1)
        timeline = np.zeros(total_samples, dtype=np.float32)

        for start_t, wav_path in tts_files:
            try:
                y, file_sr = sf.read(str(wav_path), dtype="float32")
                if file_sr != sr:
                    import librosa
                    y = librosa.resample(y, orig_sr=file_sr, target_sr=sr)
                start_sample = int(start_t * sr)
                end_sample = min(start_sample + len(y), total_samples)
                chunk = y[:end_sample - start_sample]
                timeline[start_sample:end_sample] += chunk
            except Exception as e:
                logger.warning(f"Could not mix {wav_path}: {e}")

        peak = np.max(np.abs(timeline))
        if peak > 1.0:
            timeline /= peak

        sf.write(str(out_path), timeline, sr)

    except Exception as e:
        logger.error(f"Failed to mix dubbed audio: {e}")
        if tts_files:
            shutil.copy2(str(tts_files[0][1]), str(out_path))
