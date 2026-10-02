import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from assamese_agent import media, project
from assamese_agent.cli import main
from assamese_agent.providers import sarvam_translate


class UnitTests(unittest.TestCase):
    def test_timestamps(self):
        self.assertEqual(media.timestamp(3661.007), '01:01:01,007')
        self.assertEqual(media.timestamp(59.9999), '00:01:00,000')

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            project.validate([dict(start=0, end=2, text='a'), dict(start=1, end=3, text='b')], 4)

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            project.validate([dict(start=0, end=float('nan'), text='a')], 4)

    def test_review_invalidated(self):
        p = dict(video_sha256='abc', source_language='en',
                 segments=[dict(start=0, end=1, text='Hello', assamese='নমস্কাৰ')])
        p['review'] = {'sha256': project.review_hash(p)}
        project.reviewed(p)
        p['segments'][0]['assamese'] = 'Changed'
        with self.assertRaises(ValueError):
            project.reviewed(p)

    def test_cloud_opt_in(self):
        with patch('urllib.request.urlopen') as network:
            with self.assertRaises(ValueError):
                sarvam_translate('Hello', 'en-IN')
            network.assert_not_called()

    def test_translation_response_contract(self):
        from io import BytesIO
        with patch.dict('os.environ', {'SARVAM_API_KEY': 'test-key'}):
            with patch('urllib.request.urlopen', return_value=BytesIO(
                    json.dumps({'translated_text': 'নমস্কাৰ'}).encode())) as call:
                self.assertEqual(sarvam_translate('Hello', 'en-IN', True), 'নমস্কাৰ')
                sent = json.loads(call.call_args.args[0].data)
                self.assertEqual(sent['model'], 'sarvam-translate:v1')
                self.assertEqual(sent['target_language_code'], 'as-IN')

    def test_missing_rights_stops_prepare(self):
        self.assertEqual(main(['prepare', '/does-not-exist', '--out', '/tmp/no-write',
                               '--source-language', 'en']), 1)

    def test_planner_explicitly_unimplemented(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / 'plan.json'
            self.assertEqual(main(['inspired-plan', '--brief', 'Teach fractions', '--out', str(dest)]), 0)
            self.assertEqual(project.load(dest)['status'], 'human-script-required')

    def test_url_input_rejected(self):
        with self.assertRaises(ValueError):
            media.local_video('https://example.com/movie.mp4')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg required')
class MediaIntegrationTests(unittest.TestCase):
    def test_offline_video_render(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'source.mp4'
            media.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'lavfi', '-i',
                       'color=c=navy:s=320x180:d=3', '-f', 'lavfi', '-i',
                       'sine=frequency=200:duration=3', '-c:v', 'libx264', '-pix_fmt',
                       'yuv420p', '-c:a', 'aac', '-shortest', source])
            transcript = root / 'segments.json'
            project.save([dict(start=0.2, end=1.2, text='Hello', assamese='নমস্কাৰ'),
                          dict(start=1.5, end=2.5, text='Welcome', assamese='স্বাগতম')], transcript)
            job = root / 'job'
            self.assertEqual(main(['prepare', str(source), '--out', str(job),
                                   '--source-language', 'en', '--transcript', str(transcript),
                                   '--rights-confirmed']), 0)
            p = job / 'project.json'
            self.assertEqual(main(['render', str(p), '--test-tone']), 1)
            self.assertEqual(main(['approve', str(p), '--reviewer', 'Test fixture only',
                                   '--native-reviewed']), 0)
            self.assertEqual(main(['render', str(p), '--test-tone']), 0)
            output = job / 'TEST-TONE-not-assamese.mp4'
            self.assertAlmostEqual(media.duration(output), 3, places=1)
            streams = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
                                '-show_streams', '-of', 'json', str(output)]))['streams']
            self.assertEqual([s['codec_type'] for s in streams], ['video', 'audio', 'subtitle'])
            self.assertEqual(streams[1]['tags']['language'], 'asm')
            self.assertIn('নমস্কাৰ', (job / 'assamese.srt').read_text())


if __name__ == '__main__':
    unittest.main()
