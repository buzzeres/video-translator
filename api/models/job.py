from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class JobStatus(str, Enum):
    QUEUED = "queued"
    ACQUIRING = "acquiring"
    PREPROCESSING = "preprocessing"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    DETECTING_FACES = "detecting_faces"
    ASSOCIATING_SPEAKERS = "associating_speakers"
    DETECTING_LIPS = "detecting_lips"
    TRANSLATING = "translating"
    DUBBING = "dubbing"
    LIPSYNCING = "lipsyncing"
    GENERATING_SUBTITLES = "generating_subtitles"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


STATUS_LABELS: dict[JobStatus, str] = {
    JobStatus.QUEUED: "Waiting in queue...",
    JobStatus.ACQUIRING: "Downloading / loading video...",
    JobStatus.PREPROCESSING: "Extracting audio...",
    JobStatus.TRANSCRIBING: "Transcribing speech with Whisper...",
    JobStatus.DIARIZING: "Detecting speakers...",
    JobStatus.DETECTING_FACES: "Detecting faces...",
    JobStatus.ASSOCIATING_SPEAKERS: "Matching speakers to faces...",
    JobStatus.DETECTING_LIPS: "Analyzing lip movements...",
    JobStatus.TRANSLATING: "Translating text...",
    JobStatus.DUBBING: "Synthesizing dubbed audio...",
    JobStatus.LIPSYNCING: "Applying lip-sync...",
    JobStatus.GENERATING_SUBTITLES: "Generating subtitles...",
    JobStatus.RENDERING: "Rendering final video...",
    JobStatus.COMPLETED: "Done!",
    JobStatus.FAILED: "Failed",
}


class JobRequest(BaseModel):
    video_url: Optional[str] = None
    target_language: str = "Spanish"
    generate_subtitles: bool = True
    ai_dubbing: bool = True
    voice_matching: bool = False
    lip_sync: bool = False
    keep_original_audio: bool = False


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    current_step: str = "Waiting in queue..."
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    artifacts: dict[str, str] = {}
    request: JobRequest
    uploaded_file: Optional[str] = None

    model_config = {"use_enum_values": False}
