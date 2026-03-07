from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from api.models.job import JobRequest
from config.settings import Settings


@dataclass
class PipelineContext:
    job_id: str
    request: JobRequest
    workspace: Path
    settings: Settings

    # Step outputs
    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    video_metadata: dict = field(default_factory=dict)
    transcript: Optional[dict] = None
    segments: Optional[list[dict]] = None
    source_language: Optional[str] = None
    diarization: Optional[dict[str, list[tuple[float, float]]]] = None
    face_tracks: Optional[list[dict]] = None
    lip_landmarks: Optional[dict[int, dict[str, float]]] = None
    speaker_map: Optional[dict[str, str]] = None
    translated_segments: Optional[list[dict]] = None
    dubbed_audio_path: Optional[Path] = None
    lipsynced_video_path: Optional[Path] = None
    subtitle_srt_path: Optional[Path] = None
    subtitle_vtt_path: Optional[Path] = None
    final_video_path: Optional[Path] = None
    request_uploaded_file: Optional[str] = None


class StepSkippedException(Exception):
    pass
