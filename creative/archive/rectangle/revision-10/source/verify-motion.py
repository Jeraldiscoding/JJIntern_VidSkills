#!/usr/bin/env python3
"""Verify revision10's 18s exports after rendering. Python stdlib, Node and FFmpeg only."""
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
OUTPUTS = [(120, 'JJIntern-revision10-120fps-master.mp4'), (60, 'JJIntern-revision10-60fps.mp4')]


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
    """Check each deliberate rightward shot independently of the whip reset."""
    source = (ROOT / 'source/motion.html').read_text()
    start = source.index('function flightState(')
    opening = source.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    function = source[start:end]
    expected = {'compress': 2, 'packed': 2.55, 'launch': 2.55, 'whipStart': 5.15, 'whipEnd': 5.32,
                'arrival': 7.1, 'swallowed': 7.6, 'latched': 7.82, 'settled': 8.5,
                'found': 8.5, 'payoff': 11.1, 'readable': 11.7, 'signoff': 14, 'end': 18}
    timing_matches = all(abs(scene['timeline'][k] - v) < 1e-8 for k, v in expected.items())
    packet = scene['packet']
    receiver_start = source.index('function receiverX(')
    receiver_function = source[receiver_start:source.index('}', receiver_start) + 1]
    js = ('const clamp=x=>Math.max(0,Math.min(1,x));const phase=(t,a,b)=>clamp((t-a)/(b-a));'
          'const mix=(a,b,u)=>a+(b-a)*u;const smooth=x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10)};'
          f"const T={json.dumps(scene['timeline'])},PW={packet['width']},PH={packet['height']},Y=832.5,RX=680,X0={packet['startX']},contactScale={packet['contactScale']};" + function + receiver_function +
          'console.log(JSON.stringify({shots:[[2.55,5.15-1e-6],[5.32,7.1]].map(([a,b])=>Array.from({length:121},(_,i)=>{const t=a+(b-a)*i/120;return {t,...flightState(t)}})),receiver:[7.1,7.6,7.82,8.5,9.5,11.1].map(t=>({t,x:receiverX(t)})),launch:flightState(T.launch)}));')
    actual = json.loads(run(['node', '-e', js]).stdout)
    shots = actual['shots']
    receiver_error = max(abs(p['x'] - (680 - 60 * (p['t'] - 7.1))) for p in actual['receiver'])
    morph_end_x = 540 + 55 - packet['width'] / 2
    morph_end_velocity = 110 / .55
    boundary_passed = abs(actual['launch']['x'] - morph_end_x) < 1e-8 and abs(actual['launch']['velocity'] - morph_end_velocity) < 1e-8 and scene['morph']['pause'] is False
    results = []
    for index, (samples, parameters) in enumerate(zip(shots, [(2.55, 2.6, 377.5, 702.5, 520 / 702.5, 1 - 520 / 702.5), (5.32, 1.78, -330, 680, .85, .15)]), 1):
        begin, duration, x0, distance, a, b = parameters
        errors = []
        for sample in samples:
            u = (sample['t'] - begin) / duration
            errors.extend([abs(sample['x'] - (x0 + distance * (a * u + b * u ** 3))),
                           abs(sample['velocity'] - distance / duration * (a + 3 * b * u * u))])
        increasing = all(y['x'] > x['x'] and y['velocity'] > x['velocity'] for x, y in zip(samples, samples[1:]))
        results.append({'shot': index, 'passed': max(errors) < 1e-7 and increasing and samples[0]['velocity'] > 0
                        and all(sample['shot'] == index for sample in samples),
                        'start_s': begin, 'duration_s': duration, 'screen_x_start_end': [x0, x0 + distance],
                        'speed_start_end_px_s': [samples[0]['velocity'], samples[-1]['velocity']],
                        'max_formula_error': max(errors)})
    return {'passed': timing_matches and boundary_passed and receiver_error < 1e-8 and all(shot['passed'] for shot in results), 'timeline_matches': timing_matches,
            'shots': results, 'whip_interval_s': [5.15, 5.32],
            'whip_note': 'Explicit match-on-action shot change; screen x resets during this interval and is not tested as one continuous flight.',
            'capture_interval_s': [7.1, 7.6], 'clamp_interval_s': [7.6, 7.82], 'logo_takeover_interval_s': [7.82, 8.5],
            'morph_launch_boundary': {'passed': boundary_passed, 'left_x': morph_end_x, 'velocity_px_s': morph_end_velocity, 'pause': False},
            'receiver_drift': {'passed': receiver_error < 1e-8, 'function': receiver_function, 'velocity_px_s': -60, 'samples': actual['receiver']},
            'combined_logo_bubble_interval_s': [8.5, 11.1],
            'source_function': function}


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
            'passed': clips == 0 and peak < 1 and float(data['input_tp']) <= -1}


def review_frames(path, fps):
    times = [.7, 1.9, 2.2, 2.4, 2.55 - 1 / fps, 2.55, 3.4, 4.8, 5.23, 5.8, 6.5,
             7.1, 7.3, 7.6, 7.82, 8.5, 8.75, 9.8, 10.7, 11.35, 11.7, 13.9, 14.55, 18 - 1 / fps]
    frames = [round(t * fps) for t in times]
    pattern = REVIEW / f'encoded-{fps}-frame-%02d.png'
    select = '+'.join(f'eq(n,{n})' for n in frames)
    ffmpeg('-v', 'error', '-y', '-i', path, '-an', '-vf', f"select='{select}'", '-fps_mode', 'passthrough', '-start_number', '0', pattern)
    boards = []
    for index, start in enumerate(range(0, len(frames), 8), 1):
        count = min(8, len(frames) - start)
        out = REVIEW / f'encoded-{fps}-board-{index}.png'
        ffmpeg('-v', 'error', '-y', '-framerate', '1', '-start_number', start, '-i', pattern,
               '-vf', f'scale=360:640:flags=lanczos,tile=4x{math.ceil(count / 4)}:nb_frames={count}', '-frames:v', '1', out)
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
    check(checks, 'exact18.000-second presentation', all(abs(float(s['duration']) - 18) < 1e-6 for s in (meta['format'], video, sound)),
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
    check(checks, 'decoded frame count and uniform timestamps', len(times) == 18 * fps and error < 1e-6,
          {'frames': len(times), 'expected': 18 * fps, 'last_pts': times[-1], 'max_timestamp_error_s': error})
    result = ffmpeg('-v', 'error', '-xerror', '-i', path, '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-')
    check(checks, 'full decode without errors', not result.stderr.strip(), result.stderr or 'No decoder errors')
    levels = audio(path)
    check(checks, 'encoded audio unclipped and at or below -1 dBTP', levels['passed'], levels)
    frames, boards = review_frames(path, fps)
    for label, first, last in [('source reading hold', 0, 1)]:
        delta = final_delta(frames[first]['path'], frames[last]['path'])
        check(checks, label + ' remains stable', delta < 1,
              {'mean_rgb_delta_0_255': delta, 'comparison_s': [frames[first]['time_s'], frames[last]['time_s']]})
    boundary_delta = final_delta(frames[4]['path'], frames[5]['path'])
    check(checks, 'moving morph-to-flight boundary has no large raster discontinuity', boundary_delta < 2,
          {'mean_rgb_delta_0_255': boundary_delta, 'comparison_s': [frames[4]['time_s'], frames[5]['time_s']],
           'method': 'Central action crop comparison; source endpoint position and velocity are checked separately.'})
    difference = final_delta(frames[-2]['path'], frames[-1]['path'])
    check(checks, 'signoff stable through final frame', difference < 1, {'mean_rgb_delta_0_255': difference, 'comparison_s': [14.55, (18 * fps - 1) / fps]})
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'passed': all(c['passed'] for c in checks),
            'checks': checks, 'decoded_frames': frames, 'boards': boards, 'board_order': 'Row-major; frames 0-7 on board 1, 8-15 on board 2, 16-23 on board 3'}


def main():
    missing = [name for _, name in OUTPUTS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit('Wait for final render: ' + ', '.join(missing))
    manifest = json.loads((ROOT / 'render-manifest.json').read_text())
    report = {'revision': 10, 'duration_s': 18, 'flight': source_flight(manifest['scene']), 'exports': [],
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
