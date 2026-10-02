"""Lazy-loaded model adapters. Paid/external translation is explicit opt-in."""
import json
import os
import urllib.request


class WhisperASR:
    def __init__(self, model='small', device='cpu'):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model, device=device,
                                  compute_type='int8' if device == 'cpu' else 'float16')

    def transcribe(self, audio, language):
        if language == 'as':
            raise ValueError('Assamese input ASR is not validated by this adapter. '
                             'Import a native-reviewed timestamped transcript instead.')
        segments, _ = self.model.transcribe(str(audio), language=language, vad_filter=True)
        return [dict(start=s.start, end=s.end, text=s.text.strip())
                for s in segments if s.text.strip()]


def sarvam_translate(text, source, allow_cloud=False):
    if not allow_cloud:
        raise ValueError('Cloud translation needs --allow-cloud: sends text to Sarvam and may cost money')
    if not 0 < len(text) <= 2000:
        raise ValueError('Sarvam segment must contain 1-2000 characters; split it first')
    key = os.environ.get('SARVAM_API_KEY')
    if not key:
        raise ValueError('Set SARVAM_API_KEY securely in the process environment')
    payload = dict(input=text, source_language_code=source,
                   target_language_code='as-IN', model='sarvam-translate:v1', mode='formal')
    request = urllib.request.Request('https://api.sarvam.ai/translate',
                                     data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json',
                                              'api-subscription-key': key}, method='POST')
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    result = data.get('translated_text')
    if not isinstance(result, str) or not result.strip():
        raise ValueError('Translation response contained no translated_text')
    return result.strip()


class IndicParlerVoice:
    def __init__(self, device='cpu', speaker='Sita'):
        if speaker not in ('Sita', 'Amit'):
            raise ValueError('Use a documented Assamese stock voice: Sita or Amit')
        import torch
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
        self.device = device
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(
            'ai4bharat/indic-parler-tts').to(device)
        self.tokenizer = AutoTokenizer.from_pretrained('ai4bharat/indic-parler-tts')
        self.description_tokenizer = AutoTokenizer.from_pretrained(
            self.model.config.text_encoder._name_or_path)
        self.description = (f'{speaker} speaks Assamese with a clear, natural voice, '
                            'moderate speed and a very clean, close recording.')
        self.torch = torch

    def synthesize(self, text, output):
        import soundfile as sf
        if len(text) > 500:
            raise ValueError('Split long Assamese segments into <=500 characters before synthesis')
        desc = self.description_tokenizer(self.description, return_tensors='pt').to(self.device)
        prompt = self.tokenizer(text, return_tensors='pt').to(self.device)
        with self.torch.inference_mode():
            result = self.model.generate(input_ids=desc.input_ids,
                                         attention_mask=desc.attention_mask,
                                         prompt_input_ids=prompt.input_ids,
                                         prompt_attention_mask=prompt.attention_mask)
        sf.write(str(output), result.cpu().numpy().squeeze(), self.model.config.sampling_rate)
