# Release acceptance

## Build-time result

10 automated offline tests passed in the build environment on Python 3.10.12. Test categories: subtitle timestamp rounding, non-overlap, finite timestamps, review invalidation, cloud opt-in, mocked translation contract, rights gate, planner status, local-file requirement, and a real ffmpeg synthetic-video render with video/audio/subtitle stream checks.

These tests do not establish actual Assamese speech quality. The voice model and ASR packages were not installed or run; translation used a mocked response. The offline media test uses test tones, not Assamese audio.

## Before an Assamese dubbing demo

- Clean-install dependencies; record package versions, model revision and ffmpeg build.
- Use a 30-60-second owned video with an explicit consent/rights record. No student data needed.
- Compare imported transcript with model transcript. Check names, numbers, terms and timestamps.
- Have at least two native Assamese reviewers assess translation accuracy, pronunciation, naturalness and teaching value. Keep corrections and reviewer notes.
- Check sync at sentence boundaries, silent gaps and end of video. Stop on clipped words or unnatural speed.
- Visually check the video and Assamese SRT in an Assamese-font-capable player. Soft-subtitle behavior depends on the player.
- Confirm original speech is removed; do not claim preserved background music or lip sync.
- Ensure no external provider received audio/video unexpectedly. Only Sarvam translation sends source text, and only with explicit opt-in.
- Record total processing time, peak GPU memory and any API cost before deciding infrastructure.
- Review licensing, provider terms and privacy obligations for the planned business distribution.

## Suggested quality set

Start with several speakers/accents and quiet/noisy recordings; use classroom terminology, code-mixed English terms and proper names. Split training/development/test material by speaker if future fine-tuning is approved. Native-reviewed references are essential. Track WER/CER for ASR, meaning/name/number accuracy for translation, and pronunciation/naturalness/sync judgments for TTS.

Do not invent a quality score without running and recording this evaluation. Never use a synthetic test-tone result as proof of voice generation.
