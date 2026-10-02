import hashlib
import json
import math
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(data, path):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate(segments, seconds, translated=False):
    if not isinstance(segments, list) or not 1 <= len(segments) <= 2000:
        raise ValueError('Need 1-2000 transcript segments')
    last_end = 0
    for s in segments:
        start, end = s['start'], s['end']
        if not isinstance(start, (float, int)) or not isinstance(end, (float, int)):
            raise ValueError('Timestamps must be numbers')
        if not all(math.isfinite(x) for x in (start, end)):
            raise ValueError('Non-finite timestamp')
        if start < last_end or not start < end <= seconds + 0.02:
            raise ValueError('Segments must be ordered, non-overlapping, and inside video duration')
        if not isinstance(s.get('text'), str) or not s['text'].strip():
            raise ValueError('Empty source text')
        if translated:
            text = s.get('assamese')
            if not isinstance(text, str) or not text.strip() or len(text) > 500:
                raise ValueError('Assamese text required, <=500 characters per segment')
        last_end = end


def review_hash(project):
    fields = {k: project[k] for k in ('video_sha256', 'source_language', 'segments')}
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def reviewed(project):
    if project.get('review', {}).get('sha256') != review_hash(project):
        raise ValueError('Transcript/translation needs native review. Run approve after checking it')
