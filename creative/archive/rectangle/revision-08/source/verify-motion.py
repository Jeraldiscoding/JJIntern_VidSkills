#!/usr/bin/env python3
"""Verify revision08's 18s exports after rendering. Python stdlib, Node and FFmpeg only."""
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
OUTPUTS = [(120, 'JJIntern-revision08-120fps-master.mp4'), (60, 'JJIntern-revision08-60fps.mp4')]


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
    expected_timeline = {'compress': 2, 'packed': 2.55, 'launch': 3.1, 'arrival': 8.1,
                         'swallowed': 9.05, 'latched': 9.25, 'settled': 9.85, 'found': 10.2,
                         'payoff': 11.1, 'readable': 11.7, 'signoff': 14, 'end': 18}
    timing_matches = all(abs(scene['timeline'][key] - value) < 1e-8 for key, value in expected_timeline.items())
    js = ('const clamp=x=>Math.max(0,Math.min(1,x));const phase=(t,a,b)=>clamp((t-a)/(b-a));'
          'const mix=(a,b,u)=>a+(b-a)*u;const smooth=x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10)};'
          f"const T={json.dumps(scene['timeline'])};const X0={packet['startX']},X1={packet['endX']},PW={packet['width']},PH={packet['height']},contactScale={packet['contactScale']};" + function +
          'console.log(JSON.stringify(Array.from({length:361},(_,i)=>{const t=3.1+5*i/360;return {t,...flightState(t)}})));')
    samples = json.loads(run(['node', '-e', js]).stdout)
    errors = []
    for i, s in enumerate(samples):
        u = i / 360
        expected_x = 70 + 370 * (.6 * u + .4 * u ** 3)
        expected_v = 44.4 + 88.8 * u * u
        errors.extend([abs(s['x'] - expected_x), abs(s['velocity'] - expected_v)])
    increasing = all(b['x'] > a['x'] and b['velocity'] > a['velocity'] for a, b in zip(samples, samples[1:]))
    background_increases = samples[0]['backgroundSpeed'] > 0 and all(
        b['backgroundSpeed'] > a['backgroundSpeed'] for a, b in zip(samples, samples[1:]))
    return {'passed': abs(flight['start'] - 3.1) < 1e-8 and abs(flight['end'] - 8.1) < 1e-8
                     and max(errors) < 1e-7 and increasing and samples[0]['velocity'] > 0
                     and timing_matches and background_increases
                     and abs(samples[0]['scale'] - 1) < 1e-8 and abs(samples[-1]['scale'] - .65) < 1e-8
                     and packet['width'] == 435 and packet['height'] == 255,
            'actual_function': function, 'duration_s': 5.0, 'distance_px': 370,
            'compression_duration_s': .55, 'packet_pause_duration_s': .55, 'docking_duration_s': .95, 'timeline_matches': timing_matches,
            'max_formula_error': max(errors), 'speed_start_px_s': samples[0]['velocity'],
            'speed_end_px_s': samples[-1]['velocity'], 'scale_start_end': [samples[0]['scale'], samples[-1]['scale']],
            'background_speed_px_s': [samples[0]['backgroundSpeed'], samples[-1]['backgroundSpeed']],
            'background_speed_increases': background_increases,
            'background_direction': 'Horizontal right-to-left; source reviewed',
            'sampling': {'120fps': {'first_flight': 372, 'last_flight': 971, 'first_handoff': 972},
                         '60fps': {'first_flight': 186, 'last_flight': 485, 'first_handoff': 486}},
            'contact_note': 'Contact is exactly 8.100s: frame 972 at 120fps or frame 486 at 60fps.'}


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
    times = [.7, 1.9, 2.15, 2.4, 2.65, 3.05, 3.1, 4.4, 6.2, 7.3, 8.0, 8.1,
             8.45, 8.8, 9.05, 9.25, 9.85, 10.65, 11.35, 11.7, 13.9, 14.2, 14.55, 18 - 1 / fps]
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
    for label, first, last in [('source reading hold', 0, 1), ('packed pause before launch', 4, 5)]:
        delta = final_delta(frames[first]['path'], frames[last]['path'])
        check(checks, label + ' remains stable', delta < 1,
              {'mean_rgb_delta_0_255': delta, 'comparison_s': [frames[first]['time_s'], frames[last]['time_s']]})
    difference = final_delta(frames[-2]['path'], frames[-1]['path'])
    check(checks, 'signoff stable through final frame', difference < 1, {'mean_rgb_delta_0_255': difference, 'comparison_s': [14.55, (18 * fps - 1) / fps]})
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'passed': all(c['passed'] for c in checks),
            'checks': checks, 'decoded_frames': frames, 'boards': boards, 'board_order': 'Row-major; frames 0-7 on board 1, 8-15 on board 2, 16-23 on board 3'}


def main():
    missing = [name for _, name in OUTPUTS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit('Wait for final render: ' + ', '.join(missing))
    manifest = json.loads((ROOT / 'render-manifest.json').read_text())
    report = {'revision': 8, 'duration_s': 18, 'flight': source_flight(manifest['scene']), 'exports': [],
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
