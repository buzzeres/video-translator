from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    workspace_dir: Path = Path("workspace")
    max_concurrent_jobs: int = 2

    whisper_model: str = "base"
    whisper_device: str = "cpu"

    huggingface_token: str = ""

    tts_backend: str = "coqui"
    elevenlabs_api_key: str = ""
    coqui_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"

    translation_backend: str = "deep_translator"
    openai_api_key: str = ""
    deepl_api_key: str = ""

    wav2lip_enabled: bool = False
    wav2lip_checkpoint_path: Path = Path("models/wav2lip/wav2lip_gan.pth")
    wav2lip_python_path: str = "python"

    max_upload_size_mb: int = 500

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
