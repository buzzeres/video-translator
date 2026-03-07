from __future__ import annotations
from config.settings import Settings
from config.languages import LANGUAGES


class TranslationService:
    def __init__(self, settings: Settings) -> None:
        self.backend = settings.translation_backend
        self.settings = settings

    def translate(self, text: str, target_language: str) -> str:
        if not text.strip():
            return text
        lang_config = LANGUAGES.get(target_language, {})
        if self.backend == "openai":
            return self._openai_translate(text, target_language)
        elif self.backend == "deepl":
            return self._deepl_translate(text, lang_config.get("iso", "en"))
        else:
            return self._deep_translator_translate(text, lang_config.get("deep_translator", "english"))

    def _deep_translator_translate(self, text: str, target: str) -> str:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target=target).translate(text)

    def _openai_translate(self, text: str, target_language: str) -> str:
        import openai
        client = openai.OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional translator. Translate the given text to {target_language}. "
                        "Preserve the meaning and tone exactly. Return only the translated text, nothing else."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()

    def _deepl_translate(self, text: str, target_iso: str) -> str:
        import deepl
        translator = deepl.Translator(self.settings.deepl_api_key)
        result = translator.translate_text(text, target_lang=target_iso.upper())
        return result.text
