from __future__ import annotations
import threading
from config.settings import Settings


class WhisperService:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_model(cls, settings: Settings):
        with cls._lock:
            if cls._instance is None:
                import whisper
                cls._instance = whisper.load_model(
                    settings.whisper_model,
                    device=settings.whisper_device,
                )
        return cls._instance
