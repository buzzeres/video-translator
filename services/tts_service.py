from __future__ import annotations
import threading
from pathlib import Path
from config.settings import Settings
from config.languages import LANGUAGES


class TTSService:
    _coqui_lock = threading.Lock()
    _coqui_model = None

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.backend = settings.tts_backend

    def synthesize(self, text: str, target_language: str, output_path: Path) -> Path:
        lang_config = LANGUAGES.get(target_language, {})
        tts_lang = lang_config.get("tts")
        if not tts_lang:
            tts_lang = "en"
        if self.backend == "elevenlabs":
            return self._elevenlabs_synthesize(text, output_path)
        else:
            return self._coqui_synthesize(text, tts_lang, None, output_path)

    def synthesize_cloned(self, text: str, target_language: str, speaker_wav: Path, output_path: Path) -> Path:
        lang_config = LANGUAGES.get(target_language, {})
        tts_lang = lang_config.get("tts")
        if not tts_lang:
            tts_lang = "en"
        if self.backend == "elevenlabs":
            return self._elevenlabs_synthesize(text, output_path)
        else:
            return self._coqui_synthesize(text, tts_lang, speaker_wav, output_path)

    def _coqui_synthesize(self, text: str, language: str, speaker_wav: Path | None, output_path: Path) -> Path:
        with self._coqui_lock:
            if self._coqui_model is None:
                from TTS.api import TTS
                TTSService._coqui_model = TTS(model_name=self.settings.coqui_model)

        model = self._coqui_model
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if speaker_wav and speaker_wav.exists():
            model.tts_to_file(
                text=text,
                speaker_wav=str(speaker_wav),
                language=language,
                file_path=str(output_path),
            )
        else:
            model.tts_to_file(
                text=text,
                language=language,
                file_path=str(output_path),
            )
        return output_path

    def _elevenlabs_synthesize(self, text: str, output_path: Path) -> Path:
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=self.settings.elevenlabs_api_key)
        audio = client.generate(text=text, model="eleven_multilingual_v2")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return output_path
