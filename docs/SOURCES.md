# Sources and component terms

Checked 2 October 2026. Recheck for deployment; API terms and dependencies can change.

- AI4Bharat Indic Parler-TTS: https://huggingface.co/ai4bharat/indic-parler-tts
  The model card states Apache-2.0 and includes Assamese; recommended Assamese voices are Amit and Sita. Use stock voices only. Keep upstream notices as required and review any redistribution terms. The card provides separate prompt and description tokenizers; the adapter follows that pattern.
- Parler-TTS implementation: https://github.com/huggingface/parler-tts
  This is the installation route referenced by the model card. Pin an audited revision before production; installation/inference were not validated in this scaffold build.
- Faster Whisper: https://github.com/SYSTRAN/faster-whisper
  The repository states MIT and documents `WhisperModel.transcribe`, CPU int8/CUDA examples. Verify the selected model weights and dependency terms too. Assamese-source recognition is not promised by this adapter.
- Sarvam translation: https://docs.sarvam.ai/api-reference/text/translate-text
  Documents POST `/translate`, `sarvam-translate:v1`, Assamese code `as-IN`, formal mode, maximum 2,000 input characters and `translated_text` response. A hosted API is not an open-model license. Commercial access, prices, retention and privacy require the provider's current agreement. No paid call was made during development.
- Sarvam TTS: https://docs.sarvam.ai/api-reference/text-to-speech/convert
  Its current REST language-code list does not include Assamese. Do not route Assamese voice synthesis to this API based on a general multilingual marketing claim.

FFmpeg/libx264 are system dependencies. Review the exact build's LGPL/GPL configuration and any codec/distribution obligations before bundling binaries or delivering a business product. Source inputs and outputs need their own rights review; a permissive model license does not license a protected video or a person's voice.

No open-source license is applied to eSkillVeda's new application code in this scaffold. Keep it private until the owner decides licensing and publication.
