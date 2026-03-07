from __future__ import annotations
import json
import logging
from pipeline.context import PipelineContext
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> None:
    translator = TranslationService(ctx.settings)
    target = ctx.request.target_language
    translated: list[dict] = []

    for seg in (ctx.segments or []):
        try:
            translated_text = translator.translate(seg["text"], target)
        except Exception as e:
            logger.warning(f"Translation failed for segment {seg['id']}: {e}. Keeping original.")
            translated_text = seg["text"]
        translated.append({**seg, "translated_text": translated_text})

    ctx.translated_segments = translated
    logger.info(f"Translated {len(translated)} segments to {target}")

    out_path = ctx.workspace / "translated" / "segments.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)
