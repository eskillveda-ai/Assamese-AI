# Architecture

```
Local owned video
  -> ffprobe validation and rights assertion
  -> ffmpeg mono 16 kHz audio
  -> imported timestamped transcript OR optional local Whisper ASR
  -> human source-transcript correction
  -> human translation OR opt-in Sarvam text translation
  -> native Assamese review + content hash
  -> local Indic Parler-TTS stock voice
  -> bounded timing adjustment + PCM timeline
  -> Assamese WAV + SRT + dubbed MP4
  -> final native listening/visual review
  -> manual publication outside this application
```

`cli.py` orchestrates these explicit steps. `media.py` operates ffmpeg without a shell. `project.py` validates segments and review hashes. `providers.py` loads optional adapters lazily. No model or API runs during `doctor`, file import or offline tests.

## Important limits

This v0.1 is a scaffold with a working offline pipeline, not a validated hosted agentic platform. Review approval is an operator assertion, not authenticated multi-user approval. Use only trusted local projects; this is not a secure public upload service. Model downloads require internet. Actual voice quality, model compatibility, GPU memory and generation speed must be measured in the deployment environment.

Input speech audio is removed, not source-separated. Multi-speaker diarization, background-track preservation, emotion matching, lip sync, subtitle burning and browser UI are not implemented. Native Assamese input ASR needs an IndicConformer adapter and validation. Current source transcription adapter is for other supported languages.

## Next implementation phases

1. Run clean-install and real model tests on a controlled short video. Obtain native review and fix quality issues.
2. Add offline IndicTrans2 adapter after verifying model loading/processor dependencies and source language routing. Maintain manual-translation fallback.
3. Add IndicConformer for Assamese source audio, with WER/CER checks against native-reviewed test data.
4. Add a private web UI + queue + isolated media workers. Require authenticated consent/rights assertions, upload quotas, job progress, resumable jobs and deletion controls. Protect against malicious files and ffmpeg resource abuse before accepting untrusted uploads.
5. Add an original-content planner producing a fresh Assamese script and scene list, then an owned/licensed assets renderer. No reference-video copying, no voice identity cloning, no paid generator defaults.
6. Consider tutor/RAG as a separate module using owned course content, not a requirement for dubbing.

No background jobs, external sends or bills are triggered by this roadmap.
