# Assamese AI | eSkillVeda

A review-first local MVP for translating and dubbing an owned or licensed video into Assamese. This is a command-line pipeline, not a deployed web platform or a trained new language model.

**Status:** offline media plumbing tested. Production ASR, translation and Assamese TTS adapters are implemented but have not been run end-to-end with real models in the build environment. Native Assamese listening review is still required. Inspired-video generation is a planning interface, not a video generator.

## What works

- Local video -> mono audio -> timestamped transcript (import JSON or optional faster-whisper).
- Optional Sarvam translation to Assamese, with explicit cloud/cost opt-in. You can instead type a human translation in the project JSON.
- Native-review checkpoint, tied to a hash of the video, transcript and translation.
- Assamese stock voice adapter using AI4Bharat Indic Parler-TTS, Sita or Amit. No cloning.
- Per-segment timing fit, silence between segments, separate WAV/SRT, and dubbed MP4 with optional soft subtitles.
- New-video brief/planning JSON. Original scene/script authoring and video-generation adapter remain future work.

No public uploads, automatic publishing, training, voice cloning, background paid jobs or storage service are included. Original audio is replaced completely, so music/effects are not preserved. This is voiceover dubbing, not lip sync or multi-speaker impersonation.

## Setup

Python 3.10+ and system `ffmpeg` + `ffprobe` are required.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
assamese-agent doctor
python3 -m unittest discover -s tests -v
# Optional transcription models, downloaded only when an ASR job starts:
pip install -e '.[asr]'
# Optional Assamese TTS. GPU recommended; CPU execution can be slow:
pip install -e '.[tts]'
```

The development TTS dependency follows the upstream Git repository. Before production, pin an audited commit and all package versions in a lockfile. Dependency installation and model inference have NOT been validated here; use a clean deployment environment and run the acceptance plan in `docs/EVALUATION.md`.

### 1. Prepare transcript

Use a short video you own or have permission to adapt. Confirm participant consent separately, especially when minors appear. The flag records your assertion; it is not legal verification.

```bash
assamese-agent prepare media/input.mp4 --out outputs/lesson-1 \
  --source-language en --rights-confirmed
```

Default faster-whisper model is `small` on CPU. Choose `--model large-v3 --device cuda` only after checking GPU capacity. The source can be English, Hindi or another language supported by the installed Whisper model. Assamese-source ASR is deliberately blocked by this adapter because its quality is not validated. Import a native-reviewed transcript in that case.

To bypass ASR/model download:

```bash
assamese-agent prepare media/input.mp4 --out outputs/lesson-1 \
  --source-language en --transcript examples/segments.json --rights-confirmed
```

Inputs must be local files. The MVP accepts up to 30-minute inputs and at most 2,000 ordered, non-overlapping segments. Keep segments short; Assamese text is limited to 500 characters per segment. Split long segments and review their times.

### 2. Translate

Either edit `outputs/lesson-1/project.json`, adding `assamese` to each segment, or explicitly opt into external translation. Never paste keys into chat or commit them. Set `SARVAM_API_KEY` using your normal secret manager; `.env.example` documents the field but the CLI does not automatically load it.

```bash
# This sends source text to Sarvam and may charge your account.
# Confirm provider terms, privacy policy and budget first.
assamese-agent translate outputs/lesson-1/project.json \
  --source-code en-IN --allow-cloud
```

The request explicitly selects `sarvam-translate:v1`, `formal` mode and `as-IN`, not the default model. Sarvam currently documents 22 scheduled Indian languages for this model. For other source languages, use human translation or add another verified adapter. Segments over the API limit (2,000 characters) stop instead of being truncated. Successfully translated segments are saved incrementally and existing human translations are not overwritten.

### 3. Review and synthesize

A native Assamese reviewer must check meaning, technical terms, names, numbers and pacing before approval. Every change to transcript or translation requires fresh approval.

```bash
assamese-agent approve outputs/lesson-1/project.json \
  --reviewer 'Your native Assamese reviewer' --native-reviewed
assamese-agent render outputs/lesson-1/project.json --device cuda --speaker Sita
```

Outputs: `assamese.wav`, `assamese.srt`, `assamese-dub.mp4`, per-segment WAVs and `render-report.json`. Subtitle track is optional in the player, not burnt into the picture. The input video must remain in its original path and its SHA-256 must match. Listen to the whole result before publishing. A reviewed script is not a reviewed synthesized voice.

The renderer fits speech to the original segment window. If fitting would need more than 1.35x speed, it stops and asks for a shorter translation or new timestamps rather than silently cutting words. Slower speech can leave silence. It does not guarantee lip sync. Failed jobs leave intermediate files for inspection; use a fresh output folder for a separate project.

For an entirely offline smoke test, populate Assamese text manually, approve it, then run:

```bash
assamese-agent render outputs/lesson-1/project.json --test-tone
```

This creates `TEST-TONE-not-assamese.mp4`. Its sound is a synthetic tone, NOT speech, and must never be shown as a working Assamese voice demo.

### Original inspired-video roadmap

```bash
assamese-agent inspired-plan --brief 'Explain water conservation to Class 8 students using new examples from Assam' \
  --out outputs/original-plan.json
```

This creates a planning JSON only. Next: author a new Assamese script and storyboard, review them, select owned/licensed or newly generated visuals, then connect an approved rendering adapter. Do not copy protected dialogue, frames, characters or music from the reference. Inspiration does not supply adaptation rights. Any paid generation provider or external media upload needs a separate explicit decision.

## Architecture and deployment

See `docs/ARCHITECTURE.md` for components and roadmap, `docs/EVALUATION.md` for acceptance tests, and `docs/SOURCES.md` for model/API documentation and license notes.

No credentials or user/student media should enter this repository. Keep the repo private initially. A production platform additionally needs authentication, isolated workers, private object storage, quota/budget limits, retention/deletion controls, consent records, rate limits and an audited queue. Review deployment and distribution licenses first. No hosting, GPU spend or paid account is provisioned by this scaffold.
