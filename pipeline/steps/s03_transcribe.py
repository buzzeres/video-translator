from __future__ import annotations
from pipeline.context import PipelineContext
from services.whisper_service import WhisperService


def run(ctx: PipelineContext) -> None:
    model = WhisperService.get_model(ctx.settings)
    result = model.transcribe(
        str(ctx.audio_path),
        language=None,
        word_timestamps=True,
        verbose=False,
    )
    ctx.transcript = result
    ctx.source_language = result.get("language", "en")
    ctx.segments = [
        {
            "id": i,
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "words": seg.get("words", []),
        }
        for i, seg in enumerate(result.get("segments", []))
        if seg["text"].strip()
    ]

    # Save to disk
    import json
    out_path = ctx.workspace / "transcripts" / "transcript.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"language": ctx.source_language, "segments": ctx.segments}, f, ensure_ascii=False, indent=2)
