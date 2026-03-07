from __future__ import annotations
import logging
from typing import Callable

from api.models.job import JobStatus
from pipeline.context import PipelineContext, StepSkippedException
from pipeline.steps import (
    s01_acquire, s02_preprocess, s03_transcribe,
    s04_diarize, s05_face_detect, s06_speaker_assoc,
    s07_lip_landmarks, s08_translate, s09_voice_dub,
    s10_lipsync, s11_subtitles, s12_render,
)

logger = logging.getLogger(__name__)

StepTuple = tuple[Callable, JobStatus]


def build_step_list(ctx: PipelineContext) -> list[StepTuple]:
    req = ctx.request
    steps: list[StepTuple] = [
        (s01_acquire.run, JobStatus.ACQUIRING),
        (s02_preprocess.run, JobStatus.PREPROCESSING),
        (s03_transcribe.run, JobStatus.TRANSCRIBING),
    ]
    if req.ai_dubbing or req.lip_sync:
        steps.append((s04_diarize.run, JobStatus.DIARIZING))

    if req.lip_sync:
        steps.append((s05_face_detect.run, JobStatus.DETECTING_FACES))
        steps.append((s07_lip_landmarks.run, JobStatus.DETECTING_LIPS))
        steps.append((s06_speaker_assoc.run, JobStatus.ASSOCIATING_SPEAKERS))

    steps.append((s08_translate.run, JobStatus.TRANSLATING))

    if req.ai_dubbing:
        steps.append((s09_voice_dub.run, JobStatus.DUBBING))

    if req.lip_sync and ctx.settings.wav2lip_enabled:
        steps.append((s10_lipsync.run, JobStatus.LIPSYNCING))

    if req.generate_subtitles:
        steps.append((s11_subtitles.run, JobStatus.GENERATING_SUBTITLES))

    steps.append((s12_render.run, JobStatus.RENDERING))
    return steps


def run_pipeline(ctx: PipelineContext, job_store) -> None:
    steps = build_step_list(ctx)
    total = len(steps)

    for i, (step_fn, job_status) in enumerate(steps):
        progress = int(i / total * 100)
        job_store.update(ctx.job_id, status=job_status, progress=progress)
        try:
            step_fn(ctx)
            logger.info(f"[{ctx.job_id}] Completed step: {step_fn.__module__}")
        except StepSkippedException as e:
            logger.info(f"[{ctx.job_id}] Skipped step {step_fn.__module__}: {e}")
            continue
        except Exception as e:
            logger.exception(f"[{ctx.job_id}] Step {step_fn.__module__} failed: {e}")
            job_store.update(ctx.job_id, status=JobStatus.FAILED, error=str(e))
            return

    artifacts: dict[str, str] = {}
    if ctx.final_video_path and ctx.final_video_path.exists():
        artifacts["video"] = str(ctx.final_video_path)
    if ctx.subtitle_srt_path and ctx.subtitle_srt_path.exists():
        artifacts["subtitles_srt"] = str(ctx.subtitle_srt_path)
    if ctx.subtitle_vtt_path and ctx.subtitle_vtt_path.exists():
        artifacts["subtitles_vtt"] = str(ctx.subtitle_vtt_path)

    job_store.update(ctx.job_id, status=JobStatus.COMPLETED, progress=100, artifacts=artifacts)
    logger.info(f"[{ctx.job_id}] Pipeline complete. Artifacts: {list(artifacts.keys())}")
