"""Review-first CLI. No upload, publishing, voice cloning or paid defaults."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from . import media, project


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    prep = sub.add_parser('prepare')
    prep.add_argument('video')
    prep.add_argument('--out', required=True)
    prep.add_argument('--source-language', required=True, help='ASR language e.g. en, hi; transcript import supports any language')
    prep.add_argument('--transcript', help='JSON segment list; bypasses ASR')
    prep.add_argument('--model', default='small')
    prep.add_argument('--device', default='cpu')
    prep.add_argument('--rights-confirmed', action='store_true')
    tr = sub.add_parser('translate')
    tr.add_argument('project')
    tr.add_argument('--source-code', required=True, help='Explicit Sarvam code e.g. en-IN; no auto detection')
    tr.add_argument('--allow-cloud', action='store_true')
    ap = sub.add_parser('approve')
    ap.add_argument('project')
    ap.add_argument('--reviewer', required=True)
    ap.add_argument('--native-reviewed', action='store_true')
    render = sub.add_parser('render')
    render.add_argument('project')
    render.add_argument('--device', default='cpu')
    render.add_argument('--speaker', choices=['Sita', 'Amit'], default='Sita')
    render.add_argument('--test-tone', action='store_true', help='Offline plumbing test, NOT Assamese speech')
    inspired = sub.add_parser('inspired-plan')
    inspired.add_argument('--brief', required=True, help='Your own idea/learning objective, not copied dialogue')
    inspired.add_argument('--out', required=True)
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        if a.command == 'doctor':
            print(json.dumps({'ffmpeg': shutil.which('ffmpeg'), 'ffprobe': shutil.which('ffprobe'),
                              'python': sys.version.split()[0],
                              'note': 'Only checks system tooling, not GPU/models/API credentials'}))
            media.require_tools()
            return 0
        if a.command == 'inspired-plan':
            project.save({'status': 'human-script-required', 'brief': a.brief,
                          'constraints': ['Write a new Assamese script', 'Do not copy source dialogue or shots',
                                          'Use only owned/licensed assets', 'No voice cloning'],
                          'scenes': [], 'next': 'Author scenes with Assamese narration and original visuals. '
                                               'Video generation adapter is not implemented in v0.1.'}, a.out)
            return 0
        media.require_tools()
        if a.command == 'prepare':
            if not a.rights_confirmed:
                raise ValueError('Confirm you have dubbing rights and participant consent with --rights-confirmed')
            video = media.local_video(a.video)
            out = Path(a.out).resolve()
            out.mkdir(parents=True, exist_ok=True)
            dest = out / 'project.json'
            if dest.exists():
                raise ValueError('Project exists; choose a fresh output directory')
            seconds = media.duration(video)
            if seconds > 1800:
                raise ValueError('MVP supports videos up to 30 minutes. Split this input first')
            audio = out / 'source.wav'
            media.extract(video, audio)
            if a.transcript:
                segments = project.load(a.transcript)
            else:
                from .providers import WhisperASR
                segments = WhisperASR(a.model, a.device).transcribe(audio, a.source_language)
            project.validate(segments, seconds)
            project.save(dict(schema_version=1, video=str(video), video_sha256=project.file_hash(video),
                              source_language=a.source_language, duration=seconds,
                              rights_confirmed=True, segments=segments), dest)
            print(dest)
            return 0
        data = project.load(a.project)
        if data.get('schema_version') != 1 or data.get('rights_confirmed') is not True:
            raise ValueError('Invalid project or missing rights assertion')
        project.validate(data['segments'], data['duration'])
        if a.command == 'translate':
            from .providers import sarvam_translate
            # Save incremental progress. Never overwrite an existing human translation.
            for segment in data['segments']:
                if not segment.get('assamese'):
                    segment['assamese'] = sarvam_translate(segment['text'], a.source_code, a.allow_cloud)
                    data.pop('review', None)
                    project.save(data, a.project)
            return 0
        if a.command == 'approve':
            if not a.native_reviewed or not a.reviewer.strip():
                raise ValueError('Supply reviewer name and --native-reviewed only after checking language/timing')
            project.validate(data['segments'], data['duration'], translated=True)
            data['review'] = {'reviewer': a.reviewer, 'sha256': project.review_hash(data)}
            project.save(data, a.project)
            return 0
        if a.command == 'render':
            project.validate(data['segments'], data['duration'], translated=True)
            project.reviewed(data)
            video = media.local_video(data['video'])
            if project.file_hash(video) != data['video_sha256']:
                raise ValueError('Input video changed. Prepare and review a new project')
            out = Path(a.project).resolve().parent
            if a.test_tone:
                output = out / 'TEST-TONE-not-assamese.mp4'
                voice = None
            else:
                from .providers import IndicParlerVoice
                voice = IndicParlerVoice(a.device, a.speaker)
                output = out / 'assamese-dub.mp4'
            chunks, warnings = [], []
            for i, s in enumerate(data['segments']):
                raw, fitted = out / f'voice-{i:04}.wav', out / f'fitted-{i:04}.wav'
                slot = s['end'] - s['start']
                if a.test_tone:
                    media.tone(raw, slot)
                else:
                    voice.synthesize(s['assamese'], raw)
                spoken = media.duration(raw)
                ratio = max(1.0, spoken / slot)
                if ratio > 1.35:
                    raise ValueError(f'Segment {i} needs {ratio:.2f}x speed. Shorten translation or adjust timing and re-review')
                if ratio > 1.05:
                    warnings.append(f'Segment {i}: speed {ratio:.2f}x, review intelligibility')
                media.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', raw,
                           '-af', media.atempo_chain(ratio) + f',apad,atrim=duration={slot}',
                           '-ac', 1, '-ar', 24000, '-c:a', 'pcm_s16le', fitted])
                chunks.append((s['start'], fitted))
            track = out / ('TEST-TONE.wav' if a.test_tone else 'assamese.wav')
            srt = out / 'assamese.srt'
            media.assemble(chunks, data['duration'], track)
            media.subtitles(data['segments'], srt)
            media.mux(video, track, srt, output)
            project.save({'output': str(output), 'test_tone': a.test_tone, 'warnings': warnings,
                          'publication_status': 'NOT_PUBLISHED',
                          'requires_final_native_listening_review': True}, out / 'render-report.json')
            print(output)
            return 0
    except (ValueError, KeyError, ImportError, OSError, subprocess.CalledProcessError) as exc:
        # Do not log API keys, raw payloads or subprocess stderr containing private media paths.
        print(f'Pipeline stopped: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
