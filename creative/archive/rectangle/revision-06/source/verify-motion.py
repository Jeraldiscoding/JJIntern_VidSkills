#!/usr/bin/env python3
"""Verify revision06's 12s exports after rendering. Python stdlib, Node and FFmpeg only."""
import array
import hashlib
import json
import math
import struct
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / 'review'
OUTPUTS = [(120, 'JJIntern-revision06-120fps-master.mp4'), (60, 'JJIntern-revision06-60fps.mp4')]


def run(args, binary=False):
    p = subprocess.run([str(a) for a in args], capture_output=True, text=not binary)
    if p.returncode:
        message = p.stderr.decode(errors='replace') if binary else p.stderr
        raise RuntimeError(message[-3000:])
    return p


def ffmpeg(*args, binary=False):
    return run(['ffmpeg', '-hide_banner', '-nostdin', '-threads', '2', *args], binary)


def probe(path, *args):
    return json.loads(run(['ffprobe', '-v', 'error', *args, '-of', 'json', path]).stdout)


def check(checks, name, passed, evidence):
    checks.append({'check': name, 'passed': bool(passed), 'evidence': evidence})


def source_flight(scene):
    """Execute the actual isolated flight function, then compare with the requested curve."""
    source = (ROOT / 'source/motion.html').read_text()
    start = source.index('function flightState(')
    opening = source.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    function = source[start:end]
    packet, flight = scene['packet'], scene['flight']
    expected_timeline = {'compress': 1.8, 'launch': 2.04, 'arrival': 2.64, 'settled': 2.88,
                         'found': 4.2, 'payoff': 4.82, 'readable': 5.18, 'signoff': 9.2, 'end': 12}
    timing_matches = all(abs(scene['timeline'][key] - value) < 1e-8 for key, value in expected_timeline.items())
    js = ('const clamp=x=>Math.max(0,Math.min(1,x));const phase=(t,a,b)=>clamp((t-a)/(b-a));'
          'const mix=(a,b,u)=>a+(b-a)*u;'
          f"const T={json.dumps(scene['timeline'])};const X0={packet['startX']},X1={packet['endX']};" + function +
          'console.log(JSON.stringify(Array.from({length:361},(_,i)=>{const t=2.04+.6*i/360;return {t,...flightState(t)}})));')
    samples = json.loads(run(['node', '-e', js]).stdout)
    errors = []
    for i, s in enumerate(samples):
        u = i / 360
        expected_x = 70 + 505 * (.32 * u + .68 * u ** 3)
        expected_v = 505 / .6 * (.32 + 2.04 * u * u)
        errors.extend([abs(s['x'] - expected_x), abs(s['velocity'] - expected_v)])
    increasing = all(b['x'] > a['x'] and b['velocity'] > a['velocity'] for a, b in zip(samples, samples[1:]))
    return {'passed': abs(flight['start'] - 2.04) < 1e-8 and abs(flight['end'] - 2.64) < 1e-8
                     and max(errors) < 1e-7 and increasing and samples[0]['velocity'] > 0
                     and flight.get('cameraTracking') is False and timing_matches
                     and packet['width'] == 435 and packet['height'] == 255,
            'actual_function': function, 'duration_s': .6, 'distance_px': 505,
            'compression_duration_s': .24, 'handoff_duration_s': .24, 'timeline_matches': timing_matches,
            'max_formula_error': max(errors), 'speed_start_px_s': samples[0]['velocity'],
            'speed_end_px_s': samples[-1]['velocity'], 'camera_tracking': flight.get('cameraTracking'),
            'sampling': {'120fps': {'first_flight': 245, 'last_flight': 316, 'first_handoff': 317},
                         '60fps': {'first_flight': 123, 'last_flight': 158, 'first_handoff': 159}},
            'contact_note': 'Contact is continuous time2.64s; first encoded handoff sample is ceil(2.64*fps).'}


def faststart(path):
    names = []
    with path.open('rb') as f:
        total = path.stat().st_size
        while f.tell() + 8 <= total:
            at = f.tell()
            length, kind = struct.unpack('>I4s', f.read(8))
            if length == 1:
                length = struct.unpack('>Q', f.read(8))[0]
            elif length == 0:
                length = total - at
            if length < 8:
                raise ValueError('Invalid MP4 atom')
            names.append(kind.decode('ascii', errors='replace'))
            f.seek(at + length)
    return names.index('moov') < names.index('mdat')


def audio(path):
    result = ffmpeg('-v', 'info', '-i', path, '-map', '0:a:0', '-af',
                    'loudnorm=I=-16:TP=-1:LRA=9:print_format=json', '-f', 'null', '-').stderr
    data = json.loads(result[result.rfind('{'):result.rfind('}') + 1])
    raw = ffmpeg('-v', 'error', '-i', path, '-map', '0:a:0', '-f', 'f32le', '-acodec', 'pcm_f32le', '-', binary=True).stdout
    samples = array.array('f'); samples.frombytes(raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    peak = max(abs(s) for s in samples)
    clips = sum(abs(s) >= 1 for s in samples)
    return {'integrated_lufs': float(data['input_i']), 'true_peak_dbtp': float(data['input_tp']),
            'sample_peak_dbfs': 20 * math.log10(peak), 'clipped_samples': clips,
            'decoded_samples_per_channel': len(samples) // 2,
            'note': 'AAC may emit a padded final block; presentation duration is checked separately.',
            'passed': clips == 0 and peak < 1 and float(data['input_tp']) < 0}


def review_frames(path, fps):
    frames = [round(.45 * fps), math.ceil(1.8 * fps) - 1, round(1.92 * fps), math.ceil(2.04 * fps) - 1,
              math.ceil(2.04 * fps), round(2.3 * fps), math.ceil(2.64 * fps) - 1, math.ceil(2.64 * fps),
              round(2.76 * fps), math.ceil(2.88 * fps), round(4.42 * fps), round(4.98 * fps),
              math.ceil(5.18 * fps), math.ceil(9.2 * fps) - 1, round(9.8 * fps), 12 * fps - 1]
    pattern = REVIEW / f'encoded-{fps}-frame-%02d.png'
    select = '+'.join(f'eq(n,{n})' for n in frames)
    ffmpeg('-v', 'error', '-y', '-i', path, '-an', '-vf', f"select='{select}'", '-fps_mode', 'passthrough', '-start_number', '0', pattern)
    boards = []
    for index, start in enumerate((0, 8), 1):
        out = REVIEW / f'encoded-{fps}-board-{index}.png'
        ffmpeg('-v', 'error', '-y', '-framerate', '1', '-start_number', start, '-i', pattern,
               '-vf', 'scale=360:640:flags=lanczos,tile=4x2:nb_frames=8', '-frames:v', '1', out)
        boards.append(str(out))
    return [{'index': i, 'frame': f, 'time_s': f / fps, 'path': str(REVIEW / f'encoded-{fps}-frame-{i:02d}.png')}
            for i, f in enumerate(frames)], boards


def final_delta(first, last):
    pixels = [ffmpeg('-v', 'error', '-i', p, '-vf', 'crop=1080:460:0:730', '-pix_fmt', 'rgb24',
                     '-f', 'rawvideo', '-', binary=True).stdout for p in (first, last)]
    return sum(abs(a - b) for a, b in zip(*pixels)) / len(pixels[0])


def verify(path, fps):
    checks = []
    meta = probe(path, '-show_streams', '-show_format')
    video = next(s for s in meta['streams'] if s['codec_type'] == 'video')
    sound = next(s for s in meta['streams'] if s['codec_type'] == 'audio')
    check(checks, 'exact12.000-second presentation', all(abs(float(s['duration']) - 12) < 1e-6 for s in (meta['format'], video, sound)),
          {k: s['duration'] for k, s in [('container', meta['format']), ('video', video), ('audio', sound)]})
    check(checks, '1080x1920 H264 BT709 yuv420p at expectedfps', video['width'] == 1080 and video['height'] == 1920
          and video['codec_name'] == 'h264' and video['pix_fmt'] == 'yuv420p' and Fraction(video['avg_frame_rate']) == fps
          and all(video.get(k) == 'bt709' for k in ('color_space', 'color_primaries', 'color_transfer')),
          {k: video.get(k) for k in ('width', 'height', 'codec_name', 'pix_fmt', 'avg_frame_rate', 'color_space', 'color_range')})
    check(checks, '48kHz stereo AAC and faststart', sound['codec_name'] == 'aac' and int(sound['sample_rate']) == 48000
          and sound['channels'] == 2 and faststart(path), {'codec': sound['codec_name'], 'sample_rate': sound['sample_rate'], 'channels': sound['channels'], 'faststart': faststart(path)})
    timestamps = probe(path, '-select_streams', 'v:0', '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time')['frames']
    times = [float(f['best_effort_timestamp_time']) for f in timestamps]
    error = max(abs(t - i / fps) for i, t in enumerate(times))
    check(checks, 'decoded frame count and uniform timestamps', len(times) == 12 * fps and error < 1e-6,
          {'frames': len(times), 'expected': 12 * fps, 'last_pts': times[-1], 'max_timestamp_error_s': error})
    result = ffmpeg('-v', 'error', '-xerror', '-i', path, '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-')
    check(checks, 'full decode without errors', not result.stderr.strip(), result.stderr or 'No decoder errors')
    levels = audio(path)
    check(checks, 'encoded audio below sample and true-peak clipping', levels['passed'], levels)
    frames, boards = review_frames(path, fps)
    difference = final_delta(frames[-2]['path'], frames[-1]['path'])
    check(checks, 'signoff stable through final frame', difference < 1, {'mean_rgb_delta_0_255': difference, 'comparison_s': [9.8, (12 * fps - 1) / fps]})
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'passed': all(c['passed'] for c in checks),
            'checks': checks, 'decoded_frames': frames, 'boards': boards, 'board_order': 'Row-major, first8frames on board1 and final8frames on board2'}


def main():
    missing = [name for _, name in OUTPUTS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit('Wait for final render: ' + ', '.join(missing))
    manifest = json.loads((ROOT / 'render-manifest.json').read_text())
    report = {'revision': 6, 'duration_s': 12, 'flight': source_flight(manifest['scene']), 'exports': [],
              'perceptual_review': 'Decoded frames generated; inspection must be recorded separately.',
              'pending': ['Subjective listening', 'Physical phone playback', 'Platform upload preview']}
    for fps, name in OUTPUTS:
        print('Verifying ' + name, flush=True)
        report['exports'].append(verify(ROOT / name, fps))
    report['automated_passed'] = report['flight']['passed'] and all(e['passed'] for e in report['exports'])
    (REVIEW / 'final-qa.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'automated_passed': report['automated_passed'], 'report': str(REVIEW / 'final-qa.json')}, indent=2))
    return 0 if report['automated_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
