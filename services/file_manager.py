from __future__ import annotations
import shutil
from pathlib import Path

from config.settings import Settings


class FileManager:
    def __init__(self, settings: Settings) -> None:
        self.workspace_root = settings.workspace_dir

    def create_workspace(self, job_id: str) -> Path:
        ws = self.workspace_root / job_id
        for sub in ("input", "audio", "transcripts", "translated", "tts", "lipsync", "subtitles", "output"):
            (ws / sub).mkdir(parents=True, exist_ok=True)
        return ws

    def get_workspace(self, job_id: str) -> Path:
        return self.workspace_root / job_id

    def cleanup(self, job_id: str) -> None:
        ws = self.workspace_root / job_id
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)
