# LinguaSync — AI Video Translator

> Translate any video into any language with AI dubbing, cloned voices, and burned-in subtitles.

![LinguaSync](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Multilingual%20v2-purple?style=flat-square)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## What Is This?

LinguaSync is a full-stack AI platform that takes any video — a YouTube link or an uploaded file — and produces a translated version in your chosen language. It handles everything automatically:

1. Downloads or accepts the video
2. Extracts and transcribes the speech using OpenAI Whisper
3. Detects different speakers
4. Translates the transcript
5. Synthesizes new dubbed audio using ElevenLabs
6. Generates subtitle files (SRT + VTT)
7. Renders the final video with the new audio and optional burned-in subtitles

The result is a fully dubbed, subtitled MP4 ready to stream or download — no manual editing required.

---

## Features

| Feature | Description |
|---------|-------------|
| **URL Input** | Paste any YouTube, Vimeo, or direct video link |
| **File Upload** | Drag-and-drop MP4, MOV, MKV, AVI, or WEBM |
| **17 Languages** | English, Spanish, French, Arabic, Chinese, Hindi, German, Portuguese, Japanese, Korean, Italian, Russian, Turkish, Dutch, Polish, Amharic, Swahili |
| **AI Transcription** | OpenAI Whisper — auto-detects source language, word-level timestamps |
| **Speaker Diarization** | pyannote.audio separates multiple speakers (requires free HuggingFace token) |
| **AI Dubbing** | ElevenLabs Multilingual v2 — natural, expressive speech synthesis |
| **Voice Matching** | Coqui XTTS v2 zero-shot voice cloning from original speaker audio |
| **Subtitle Generation** | SRT and VTT files with accurate timestamps |
| **Subtitle Burn-in** | Subtitles rendered directly into the video |
| **Keep Original Audio** | Mix the original audio quietly beneath the dubbed track |
| **Lip-Sync** | Wav2Lip integration (advanced — requires manual setup, see below) |
| **Live Progress Tracking** | Real-time pipeline step indicators in the browser |
| **Video Streaming** | HTTP range-request streaming for instant browser playback |

---

## Screenshots

### Main Interface
The two-column dark UI with feature toggles and a live "How it works" panel on the right.

### Processing Screen
A live pipeline tracker showing each step (Download → Extract → Transcribe → Translate → Dub → Render) lighting up in real time.

### Results Screen
Side-by-side video player with embedded subtitles and download buttons for the video, SRT, and VTT files.

---

## Project Structure

```
video-translator/
│
├── app.py                        # FastAPI app entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Configuration template
├── .gitignore
│
├── config/
│   ├── settings.py               # All settings via Pydantic + .env
│   └── languages.py              # Language name → code mappings
│
├── api/
│   ├── router.py                 # Mounts all API routes
│   ├── models/
│   │   └── job.py                # JobRequest, JobRecord, JobStatus models
│   └── endpoints/
│       ├── jobs.py               # POST /jobs, GET /jobs/{id}, GET /jobs/{id}/status
│       ├── upload.py             # POST /upload  (multipart file)
│       ├── stream.py             # GET /stream/{job_id}  (range-request video)
│       └── download.py           # GET /download/{job_id}/{artifact}
│
├── pipeline/
│   ├── context.py                # PipelineContext dataclass — shared state
│   ├── orchestrator.py           # Runs all 12 steps, manages job state machine
│   └── steps/
│       ├── s01_acquire.py        # yt-dlp download or uploaded file copy
│       ├── s02_preprocess.py     # ffmpeg: extract 16kHz mono WAV
│       ├── s03_transcribe.py     # Whisper transcription + timestamps
│       ├── s04_diarize.py        # Speaker diarization (pyannote or fallback)
│       ├── s05_face_detect.py    # MediaPipe face detection (lip-sync only)
│       ├── s06_speaker_assoc.py  # Match speakers to faces
│       ├── s07_lip_landmarks.py  # Mouth openness tracking per frame
│       ├── s08_translate.py      # Text translation
│       ├── s09_voice_dub.py      # TTS synthesis + audio timeline mixing
│       ├── s10_lipsync.py        # Wav2Lip subprocess (scaffolded)
│       ├── s11_subtitles.py      # SRT + VTT generation
│       └── s12_render.py         # ffmpeg final video composition
│
├── services/
│   ├── job_store.py              # Thread-safe in-memory job registry
│   ├── file_manager.py           # Per-job workspace directory management
│   ├── whisper_service.py        # Whisper model singleton
│   ├── tts_service.py            # TTS abstraction (ElevenLabs / Coqui)
│   └── translation_service.py   # Translation abstraction (Google / OpenAI / DeepL)
│
├── workers/
│   └── job_runner.py             # ThreadPoolExecutor background job runner
│
├── static/
│   └── index.html                # Complete single-page frontend (vanilla JS)
│
└── workspace/                    # Auto-created — per-job working directories
    └── {job_id}/
        ├── input/                # Original video
        ├── audio/                # Extracted WAV + dubbed audio
        ├── transcripts/          # Whisper JSON output
        ├── translated/           # Translated segments JSON
        ├── tts/                  # Per-segment synthesized audio files
        ├── subtitles/            # .srt and .vtt files
        └── output/               # Final rendered video
```

---

## How the Pipeline Works

Every translation job runs through up to 12 sequential steps. Steps are automatically skipped if the corresponding feature is disabled.

```
Video URL / File Upload
        │
        ▼
 [1] s01_acquire      — yt-dlp downloads URL, or copies uploaded file
        │
        ▼
 [2] s02_preprocess   — ffmpeg extracts audio as 16kHz mono WAV (required by Whisper)
                        also reads video metadata (fps, duration, resolution)
        │
        ▼
 [3] s03_transcribe   — OpenAI Whisper transcribes speech with word-level timestamps
                        auto-detects the source language
        │
        ▼
 [4] s04_diarize      — pyannote.audio separates speakers (SPEAKER_00, SPEAKER_01, ...)
                        falls back to single-speaker mode if no HuggingFace token
        │
        ▼  (only if lip_sync=True)
 [5] s05_face_detect  — MediaPipe detects & tracks faces per video frame
 [7] s07_lip_landmarks— MediaPipe FaceMesh measures mouth openness ratio per frame
 [6] s06_speaker_assoc— Matches each speaker ID to a face by lip activity timing
        │
        ▼
 [8] s08_translate    — Translates each segment into the target language
                        backends: Google Translate (free), OpenAI GPT, or DeepL
        │
        ▼  (only if ai_dubbing=True)
 [9] s09_voice_dub    — ElevenLabs (or Coqui XTTS v2) synthesizes one audio clip per segment
                        librosa time-stretches each clip to match original segment duration
                        all clips are mixed onto a silent timeline → dubbed.wav
        │
        ▼  (only if lip_sync=True AND Wav2Lip configured)
[10] s10_lipsync      — Wav2Lip subprocess animates mouth regions to match dubbed audio
        │
        ▼  (only if generate_subtitles=True)
[11] s11_subtitles    — Writes subtitles.srt and subtitles.vtt from translated segments
        │
        ▼
[12] s12_render       — ffmpeg composes the final video:
                        • replaces/mixes audio track
                        • burns in subtitles (optional)
                        • outputs final.mp4
        │
        ▼
   COMPLETED — artifacts available for streaming and download
```

---

## Quick Start

### Prerequisites

- Python 3.11 or 3.12 (recommended — some ML packages lag behind 3.13)
- ffmpeg installed and on PATH
- Git

### 1. Install ffmpeg

**Windows:**
```bash
winget install Gyan.FFmpeg
# Restart your terminal after installation
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 2. Clone the repo

```bash
git clone https://github.com/buzzeres/video-translator.git
cd video-translator
```

### 3. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first install takes a few minutes. Coqui TTS pulls in heavy dependencies (~1 GB). If you hit PyTorch conflicts, install torch first:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

### 5. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys (see [Configuration](#configuration) below).

### 6. Run

```bash
python app.py
```

Open **http://localhost:8000** in your browser.

---

## Configuration

All settings live in `.env`. Copy `.env.example` to get started.

```env
# ── Server ────────────────────────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
WORKSPACE_DIR=workspace
MAX_CONCURRENT_JOBS=2

# ── Whisper ───────────────────────────────────────────────────────────────────
# Model size — tradeoff between speed and accuracy
# Options: tiny | base | small | medium | large-v3
WHISPER_MODEL=base
WHISPER_DEVICE=cpu         # cpu or cuda (if you have an NVIDIA GPU)

# ── Speaker Diarization ───────────────────────────────────────────────────────
# Without this, all speech is treated as one speaker.
# 1. Create a free account at https://huggingface.co
# 2. Get a token at https://huggingface.co/settings/tokens
# 3. Accept the model terms at https://hf.co/pyannote/speaker-diarization-3.1
# 4. Uncomment pyannote.audio in requirements.txt and pip install it
HUGGINGFACE_TOKEN=

# ── TTS Backend ───────────────────────────────────────────────────────────────
# coqui     = free, runs locally, slower, supports voice cloning
# elevenlabs = best quality, requires paid API key
TTS_BACKEND=elevenlabs
ELEVENLABS_API_KEY=your_key_here

# ── Translation Backend ───────────────────────────────────────────────────────
# deep_translator = free, uses Google Translate, no key needed
# openai          = GPT-4o-mini, higher quality, requires API key
# deepl           = professional quality, requires API key
TRANSLATION_BACKEND=deep_translator
OPENAI_API_KEY=
DEEPL_API_KEY=

# ── Lip-Sync (Advanced) ───────────────────────────────────────────────────────
WAV2LIP_ENABLED=false
WAV2LIP_CHECKPOINT_PATH=models/wav2lip/wav2lip_gan.pth
WAV2LIP_PYTHON_PATH=python

MAX_UPLOAD_SIZE_MB=500
```

---

## API Reference

The backend exposes a REST API. FastAPI auto-generates interactive docs at **http://localhost:8000/docs**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/jobs` | Start a job from a video URL |
| `POST` | `/upload` | Start a job from an uploaded file |
| `GET` | `/jobs/{id}` | Get full job record |
| `GET` | `/jobs/{id}/status` | Lightweight poll — status, progress, current step |
| `GET` | `/jobs` | List all jobs |
| `DELETE` | `/jobs/{id}` | Cancel job and clean up workspace |
| `GET` | `/stream/{id}` | HTTP range-request video stream (for `<video>` tag) |
| `GET` | `/download/{id}/video` | Download final MP4 |
| `GET` | `/download/{id}/subtitles_srt` | Download SRT file |
| `GET` | `/download/{id}/subtitles_vtt` | Download VTT file |
| `GET` | `/languages` | List supported language names |

### Example: Start a job via curl

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "target_language": "Spanish",
    "generate_subtitles": true,
    "ai_dubbing": true,
    "voice_matching": false,
    "lip_sync": false,
    "keep_original_audio": false
  }'
```

### Poll for status

```bash
curl http://localhost:8000/jobs/{job_id}/status
```

```json
{
  "status": "dubbing",
  "progress": 72,
  "current_step": "Synthesizing dubbed audio...",
  "error": null
}
```

---

## Optional: Wav2Lip Lip-Sync Setup

Lip-sync animates the speaker's mouth to match the translated audio. It uses [Wav2Lip](https://github.com/Rudrabha/Wav2Lip), which cannot be installed via pip and requires manual setup.

```bash
# 1. Clone Wav2Lip into the project root
git clone https://github.com/Rudrabha/Wav2Lip.git

# 2. Download the pretrained GAN checkpoint
# Link: https://iiitaphyd-my.sharepoint.com/personal/radrabha_m_research_iiit_ac_in/...
# Place the file at:
mkdir -p models/wav2lip
# → models/wav2lip/wav2lip_gan.pth

# 3. Install Wav2Lip dependencies
cd Wav2Lip
pip install -r requirements.txt
pip install batch_face    # Windows-compatible face detection backend
cd ..

# 4. Enable in .env
WAV2LIP_ENABLED=true
WAV2LIP_CHECKPOINT_PATH=models/wav2lip/wav2lip_gan.pth
```

> Wav2Lip is slow on CPU. A GPU is strongly recommended for lip-sync.

---

## Optional: Speaker Diarization Setup

By default, all speech is attributed to a single speaker. To enable multi-speaker detection:

```bash
# 1. Uncomment in requirements.txt:
#    pyannote.audio>=3.1.0

pip install pyannote.audio

# 2. Get a free HuggingFace token:
#    https://huggingface.co/settings/tokens

# 3. Accept model terms:
#    https://hf.co/pyannote/speaker-diarization-3.1

# 4. Add to .env:
HUGGINGFACE_TOKEN=hf_your_token_here
```

---

## Performance Notes

All benchmarks are on CPU (no GPU). Times are approximate for a **3-minute video**.

| Step | Approx. Time |
|------|-------------|
| Download (YouTube) | 10–30 sec |
| Audio extraction (ffmpeg) | 2–5 sec |
| Whisper `base` transcription | 3–6 min |
| Translation (Google Translate) | 5–15 sec |
| ElevenLabs dubbing (10 segments) | 20–40 sec |
| Subtitle generation | < 1 sec |
| ffmpeg render | 20–60 sec |
| **Total (subtitles + dubbing)** | **~5–10 min** |

**To speed things up:**
- Use `WHISPER_MODEL=tiny` for fast testing (lower accuracy)
- Use `WHISPER_MODEL=small` for a good accuracy/speed balance
- Use `WHISPER_DEVICE=cuda` if you have an NVIDIA GPU — speeds up transcription 10–20x

---

## Supported Languages

| Language | Code | TTS Support |
|----------|------|-------------|
| English | en | ElevenLabs, Coqui |
| Spanish | es | ElevenLabs, Coqui |
| French | fr | ElevenLabs, Coqui |
| German | de | ElevenLabs, Coqui |
| Portuguese | pt | ElevenLabs, Coqui |
| Italian | it | ElevenLabs, Coqui |
| Chinese | zh | ElevenLabs, Coqui |
| Japanese | ja | ElevenLabs, Coqui |
| Korean | ko | ElevenLabs, Coqui |
| Arabic | ar | ElevenLabs, Coqui |
| Hindi | hi | ElevenLabs, Coqui |
| Russian | ru | ElevenLabs, Coqui |
| Turkish | tr | ElevenLabs, Coqui |
| Dutch | nl | ElevenLabs, Coqui |
| Polish | pl | ElevenLabs, Coqui |
| Amharic | am | Translation only (no TTS) |
| Swahili | sw | Translation only (no TTS) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Frontend** | Vanilla HTML/CSS/JavaScript (no build step) |
| **Video Download** | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| **Video Processing** | [ffmpeg](https://ffmpeg.org/) via ffmpeg-python |
| **Speech Recognition** | [OpenAI Whisper](https://github.com/openai/whisper) |
| **Speaker Diarization** | [pyannote.audio 3.1](https://github.com/pyannote/pyannote-audio) |
| **Face Detection** | [MediaPipe](https://mediapipe.dev/) |
| **Translation** | [deep-translator](https://github.com/nidhaloff/deep-translator) / OpenAI / DeepL |
| **Text-to-Speech** | [ElevenLabs](https://elevenlabs.io/) / [Coqui XTTS v2](https://github.com/coqui-ai/TTS) |
| **Lip-Sync** | [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) |
| **Audio Processing** | librosa + soundfile + numpy |
| **Background Jobs** | Python ThreadPoolExecutor |
| **Config** | pydantic-settings + .env |

---

## Development Notes

### Adding a new language

Edit `config/languages.py` and add an entry:

```python
"Yoruba": {"iso": "yo", "whisper": "yo", "tts": None, "deep_translator": "yoruba"},
```

Set `"tts": None` if ElevenLabs / Coqui don't support it yet — the system will still translate and generate subtitles.

### Adding a new TTS backend

1. Add a new method `_mybackend_synthesize()` in `services/tts_service.py`
2. Add the backend name to the `if/elif` chain in `synthesize()` and `synthesize_cloned()`
3. Add the API key setting to `config/settings.py` and `.env.example`

### Job state machine

Jobs transition through these states in order:

```
queued → acquiring → preprocessing → transcribing → diarizing →
detecting_faces → associating_speakers → detecting_lips →
translating → dubbing → lipsyncing → generating_subtitles →
rendering → completed
```

Any step can transition to `failed` with an error message stored on the job record.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `[WinError 2] The system cannot find the file specified` | ffmpeg not in PATH | Install ffmpeg via `winget install Gyan.FFmpeg` and restart terminal |
| `ModuleNotFoundError: No module named 'pydantic_settings'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `'ElevenLabs' object has no attribute 'generate'` | ElevenLabs SDK v2 changed API | Update to latest code — fixed in this repo |
| `No module named 'websockets.asyncio'` | websockets version too old | Run `pip install "websockets>=13.0"` |
| Whisper very slow | Running on CPU | Set `WHISPER_MODEL=tiny` for testing, or use a GPU |
| Translation is wrong | Google Translate has limits | Switch to `TRANSLATION_BACKEND=openai` for better quality |

---

## License

MIT — free to use, modify, and distribute.

---

## Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) — speech recognition
- [ElevenLabs](https://elevenlabs.io/) — voice synthesis
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — video downloading
- [Coqui TTS](https://github.com/coqui-ai/TTS) — open-source voice synthesis
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — speaker diarization
- [Wav2Lip](https://github.com/Rudrabha/Wav2Lip) — lip synchronization
- [MediaPipe](https://mediapipe.dev/) — face and landmark detection
- [FastAPI](https://fastapi.tiangolo.com/) — web framework
