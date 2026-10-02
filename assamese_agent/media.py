"""Local media helpers. No shell evaluation or network media inputs."""
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave
from array import array


def run(args):
    subprocess.run([str(x) for x in args], check=True, capture_output=True)


def require_tools():
    missing = [x for x in ('ffmpeg', 'ffprobe') if not shutil.which(x)]
    if missing:
        raise ValueError('Missing system tools: ' + ', '.join(missing))


def local_video(value):
    path = Path(value).resolve()
    if not path.is_file():
        raise ValueError('Input must be an existing local video file, not a URL')
    return path


def duration(path):
    data = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                   'format=duration', '-of', 'json', str(path)])
    result = float(json.loads(data)['format']['duration'])
    if not math.isfinite(result) or result <= 0:
        raise ValueError('Invalid media duration')
    return result


def extract(video, output):
    run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', video, '-vn', '-ac', 1,
         '-ar', 16000, output])


def atempo_chain(rate):
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError('Invalid tempo')
    parts = []
    while rate > 2:
        parts.append('atempo=2')
        rate /= 2
    while rate < 0.5:
        parts.append('atempo=0.5')
        rate /= 0.5
    parts.append(f'atempo={rate:.8f}')
    return ','.join(parts)


def timestamp(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def subtitles(segments, output):
    body = '\n\n'.join(f'{i}\n{timestamp(s["start"])} --> {timestamp(s["end"])}\n'
                        + s['assamese'].replace('\r', ' ').replace('\n', ' ')
                        for i, s in enumerate(segments, 1))
    Path(output).write_text(body + '\n', encoding='utf-8')


def tone(output, seconds, sr=24000):
    """Synthetic TEST tone, never represented as a voice."""
    values = array('h', (int(2500 * math.sin(2 * math.pi * 440 * i / sr))
                         for i in range(round(seconds * sr))))
    with wave.open(str(output), 'wb') as f:
        f.setparams((1, 2, sr, 0, 'NONE', 'not compressed'))
        f.writeframes(values.tobytes())


def assemble(chunks, video_seconds, output):
    """Place bounded mono PCM chunks on a silent timeline, without input speech."""
    sr = 24000
    timeline = array('h', [0]) * round(video_seconds * sr)
    for start, path in chunks:
        with wave.open(str(path), 'rb') as f:
            if (f.getnchannels(), f.getsampwidth(), f.getframerate()) != (1, 2, sr):
                raise ValueError('Expected 24kHz mono PCM chunks')
            data = array('h')
            data.frombytes(f.readframes(f.getnframes()))
        offset = round(start * sr)
        size = min(len(data), max(0, len(timeline) - offset))
        timeline[offset:offset + size] = data[:size]
    with wave.open(str(output), 'wb') as f:
        f.setparams((1, 2, sr, 0, 'NONE', 'not compressed'))
        f.writeframes(timeline.tobytes())


def mux(video, audio, srt, output):
    run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', video, '-i', audio,
         '-i', srt, '-map', '0:v:0', '-map', '1:a:0', '-map', '2:s:0',
         '-c:v', 'libx264', '-preset', 'fast', '-crf', 20, '-c:a', 'aac',
         '-c:s', 'mov_text', '-metadata:s:a:0', 'language=asm',
         '-metadata:s:s:0', 'language=asm', '-t', video_seconds_string(video),
         '-movflags', '+faststart', output])


def video_seconds_string(video):
    return str(duration(video))
