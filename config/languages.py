LANGUAGES: dict[str, dict] = {
    "English":    {"iso": "en", "whisper": "en", "tts": "en", "deep_translator": "english"},
    "Spanish":    {"iso": "es", "whisper": "es", "tts": "es", "deep_translator": "spanish"},
    "French":     {"iso": "fr", "whisper": "fr", "tts": "fr", "deep_translator": "french"},
    "German":     {"iso": "de", "whisper": "de", "tts": "de", "deep_translator": "german"},
    "Portuguese": {"iso": "pt", "whisper": "pt", "tts": "pt", "deep_translator": "portuguese"},
    "Italian":    {"iso": "it", "whisper": "it", "tts": "it", "deep_translator": "italian"},
    "Chinese":    {"iso": "zh", "whisper": "zh", "tts": "zh-cn", "deep_translator": "chinese (simplified)"},
    "Japanese":   {"iso": "ja", "whisper": "ja", "tts": "ja", "deep_translator": "japanese"},
    "Korean":     {"iso": "ko", "whisper": "ko", "tts": "ko", "deep_translator": "korean"},
    "Arabic":     {"iso": "ar", "whisper": "ar", "tts": "ar", "deep_translator": "arabic"},
    "Hindi":      {"iso": "hi", "whisper": "hi", "tts": "hi", "deep_translator": "hindi"},
    "Russian":    {"iso": "ru", "whisper": "ru", "tts": "ru", "deep_translator": "russian"},
    "Turkish":    {"iso": "tr", "whisper": "tr", "tts": "tr", "deep_translator": "turkish"},
    "Dutch":      {"iso": "nl", "whisper": "nl", "tts": "nl", "deep_translator": "dutch"},
    "Polish":     {"iso": "pl", "whisper": "pl", "tts": "pl", "deep_translator": "polish"},
    "Amharic":    {"iso": "am", "whisper": "am", "tts": None,  "deep_translator": "amharic"},
    "Swahili":    {"iso": "sw", "whisper": "sw", "tts": None,  "deep_translator": "swahili"},
}

LANGUAGE_NAMES = sorted(LANGUAGES.keys())
