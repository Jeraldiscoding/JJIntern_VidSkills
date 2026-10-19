#!/usr/bin/env python3
"""Verify revision11's 18s exports after rendering. Python stdlib, Node and FFmpeg only."""
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
OUTPUTS = [(120, 'JJIntern-revision11-120fps-master.mp4'), (60, 'JJIntern-revision11-60fps.mp4')]


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
    """Execute the source geometry independently of browser rendering."""
    source = (ROOT / 'source/motion.html').read_text()

    def extract(name):
        start = source.index('function ' + name + '(')
        opening = source.index('{', start)
        depth, end = 1, opening + 1
        while depth:
            depth += (source[end] == '{') - (source[end] == '}')
            end += 1
        return source[start:end]

    expected = {'compress': 2, 'packed': 2.55, 'launch': 2.55, 'approach': 6.55,
                'arrival': 8.05, 'swallowed': 8.75, 'latched': 8.88, 'settled': 9.05,
                'found': 9.05, 'payoff': 9.9, 'readable': 10.5, 'signoff': 14, 'end': 18}
    timing_matches = all(abs(scene['timeline'][k] - v) < 1e-8 for k, v in expected.items())
    packet = scene['packet']
    functions = ''.join(extract(n) for n in ['fieldSpeed', 'flightState', 'receiverX', 'received'])
    js = ('const clamp=x=>Math.max(0,Math.min(1,x));const phase=(t,a,b)=>clamp((t-a)/(b-a));'
          'const mix=(a,b,u)=>a+(b-a)*u;const smooth=x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10)};'
          f"const T={json.dumps(scene['timeline'])},PW={packet['width']},PH={packet['height']},Y=832.5,RX=619.5,RW=340,RH=300,RY=810,X0={packet['startX']},contactScale={packet['contactScale']};"
          'let renderedLogo;const C={paper:"white",ink:"black"},font="sans-serif";'
          'const ctx=new Proxy({measureText:()=>({width:100})},{get:(o,k)=>o[k]||(()=>{})});'
          'const alpha=(a,f)=>{if(a>0)f()},speedField=()=>{},receiverShell=()=>{},rr=()=>{},text=()=>{};'
          'const logoPlane=(x,y,size)=>{renderedLogo={x,y,size}};'
          + functions +
          'const samples=(a,b)=>Array.from({length:121},(_,i)=>{const t=a+(b-a)*i/120;return {t,...flightState(t),receiverX:receiverX(t)}});'
          'console.log(JSON.stringify({flight:samples(2.55,6.55),approach:samples(6.55,8.05),'
          'receiver:[8.05,8.4,8.75,9.05].map(t=>({t,x:receiverX(t)})),'
          'found:[9.25,9.5,9.7].map(t=>{received(t);return {t,...renderedLogo}})}));')
    actual = json.loads(run(['node', '-e', js]).stdout)
    fixed_error = max(max(abs(p['x'] - 142.5), abs(p['y'] - 832.5), abs(p['scale'] - 1), abs(p['velocity'])) for p in actual['flight'])
    speeds = [p['backgroundSpeed'] for p in actual['flight']]
    smooth = lambda q: q ** 3 * (q * (q * 6 - 15) + 10)
    approach_error = 0
    for p in actual['approach']:
        q = smooth((p['t'] - 6.55) / 1.5)
        approach_error = max(approach_error, abs(p['x'] - (142.5 + 42 * q)), abs(p['receiverX'] - (1120 + (619.5 - 1120) * q)))
    contact = actual['approach'][-1]
    contact_gap = contact['receiverX'] - contact['x'] - packet['width']
    receiver_error = max(abs(p['x'] - (619.5 + (370 - 619.5) * smooth(min(1, (p['t'] - 8.05) / .7)))) for p in actual['receiver'])
    found_error = max(max(abs(p['x'] - 540), abs(p['y'] - 960), abs(p['size'] - 380)) for p in actual['found'])
    checks = []
    check(checks, 'final timeline matches', timing_matches, expected)
    check(checks, 'packet fixed during four-second flight', fixed_error < 1e-8,
          {'interval_s': [2.55, 6.55], 'position': [142.5, 832.5], 'scale': 1, 'max_geometry_error': fixed_error})
    check(checks, 'background accelerates while packet stays fixed', all(b > a for a, b in zip(speeds, speeds[1:])),
          {'speed_start_end_px_s': [speeds[0], speeds[-1]], 'whip': scene['flight']['whip']})
    check(checks, 'packet and receiver converge to exact contact', approach_error < 1e-7 and abs(contact_gap) < 1e-7,
          {'approach_interval_s': [6.55, 8.05], 'max_formula_error': approach_error, 'contact_gap_px': contact_gap})
    check(checks, 'receiver reaches centred logo before Found', receiver_error < 1e-7 and abs(actual['receiver'][-1]['x'] + 170 - 540) < 1e-8,
          {'samples': actual['receiver'], 'logo_center_x': 540, 'packet_occlusion_lip_offset_px': 22})
    check(checks, 'settled logo fixed throughout short Found hold', found_error < 1e-8 and scene['found']['standaloneTitle'] is False,
          {'logo_calls_from_actual_received_function': actual['found'], 'bubble_interval_s': [9.05, 9.9], 'fade_interval_s': [9.72, 9.9]})
    return {'passed': all(c['passed'] for c in checks), 'checks': checks,
            'method': 'Executed flightState, fieldSpeed, receiverX and received from final motion.html; decoded frames verify appearance.'}


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
    times = [.7, 1.9, 2.2, 2.4, 2.55, 3.2, 4.7, 6.4,
             6.55, 7.1, 7.7, 8.05, 8.3, 8.6, 8.75, 9.05,
             9.3, 9.65, 10.15, 10.5, 12.5, 13.9, 14.55, 18 - 1 / fps]
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


def final_delta(first, last, crop="1080:460:0:730"):
    pixels = [ffmpeg('-v', 'error', '-i', p, '-vf', 'crop=' + crop, '-pix_fmt', 'rgb24',
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
    for label, first, last, crop in [
            ('stationary flight packet interior', 5, 7, '390:210:165:855'),
            ('stationary settled logo and Found bubble', 16, 17, '600:550:240:650')]:
        delta = final_delta(frames[first]['path'], frames[last]['path'], crop)
        check(checks, label + ' remains stable', delta < 1,
              {'mean_rgb_delta_0_255': delta, 'comparison_s': [frames[first]['time_s'], frames[last]['time_s']],
               'crop_width_height_x_y': crop, 'note': 'Geometry is also checked by executing the source functions.'})
    difference = final_delta(frames[-2]['path'], frames[-1]['path'])
    check(checks, 'signoff stable through final frame', difference < 1, {'mean_rgb_delta_0_255': difference, 'comparison_s': [14.55, (18 * fps - 1) / fps]})
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'passed': all(c['passed'] for c in checks),
            'checks': checks, 'decoded_frames': frames, 'boards': boards, 'board_order': 'Row-major; frames 0-7 on board 1, 8-15 on board 2, 16-23 on board 3'}


def main():
    missing = [name for _, name in OUTPUTS if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit('Wait for final render: ' + ', '.join(missing))
    manifest = json.loads((ROOT / 'render-manifest.json').read_text())
    report = {'revision': 11, 'duration_s': 18, 'flight': source_flight(manifest['scene']), 'exports': [],
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
