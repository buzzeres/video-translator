from __future__ import annotations
import logging
from pipeline.context import PipelineContext, StepSkippedException

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    if not ctx.request.lip_sync:
        raise StepSkippedException("lip_sync disabled")
    if not ctx.diarization or not ctx.lip_landmarks:
        ctx.speaker_map = {}
        return

    fps = ctx.video_metadata.get("fps", 25.0)
    speaker_map: dict[str, str] = {}

    for speaker_id, time_ranges in ctx.diarization.items():
        activity: dict[str, float] = {}
        for start, end in time_ranges:
            frame_start = int(start * fps)
            frame_end = int(end * fps)
            for frame_idx in range(frame_start, frame_end + 1):
                frame_data = ctx.lip_landmarks.get(frame_idx, {})
                for face_id, openness in frame_data.items():
                    activity[face_id] = activity.get(face_id, 0.0) + openness

        if activity:
            best_face = max(activity, key=activity.__getitem__)
            speaker_map[speaker_id] = best_face
        else:
            speaker_map[speaker_id] = "FACE_00"

    ctx.speaker_map = speaker_map
    logger.info(f"Speaker-face mapping: {speaker_map}")
