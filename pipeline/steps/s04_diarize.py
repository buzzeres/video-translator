from __future__ import annotations
import logging
from pipeline.context import PipelineContext, StepSkippedException

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    if ctx.settings.huggingface_token:
        try:
            _diarize_pyannote(ctx)
            return
        except ImportError:
            logger.warning("pyannote.audio not installed. Using fallback diarization.")
        except Exception as e:
            logger.warning(f"pyannote diarization failed: {e}. Using fallback.")
    _diarize_fallback(ctx)


def _diarize_pyannote(ctx: PipelineContext) -> None:
    from pyannote.audio import Pipeline as PyannotePipeline

    pipeline = PyannotePipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=ctx.settings.huggingface_token,
    )
    diarization = pipeline(str(ctx.audio_path))

    result: dict[str, list[tuple[float, float]]] = {}
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        result.setdefault(speaker, []).append((turn.start, turn.end))

    ctx.diarization = result
    logger.info(f"Diarization found {len(result)} speakers.")


def _diarize_fallback(ctx: PipelineContext) -> None:
    if not ctx.segments:
        ctx.diarization = {}
        return
    ctx.diarization = {
        "SPEAKER_00": [(seg["start"], seg["end"]) for seg in ctx.segments]
    }
    logger.info("Using single-speaker fallback diarization.")


def get_speaker_for_segment(segment: dict, diarization: dict[str, list[tuple[float, float]]]) -> str:
    if not diarization:
        return "SPEAKER_00"
    seg_mid = (segment["start"] + segment["end"]) / 2
    best_speaker = "SPEAKER_00"
    for speaker, ranges in diarization.items():
        for start, end in ranges:
            if start <= seg_mid <= end:
                return speaker
    return best_speaker
