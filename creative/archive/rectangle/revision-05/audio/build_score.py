#!/usr/bin/env python3
"""Original revision-05 score: deterministic mathematical synthesis, no samples.

Run with the standard Python library and local FFmpeg:
    python3 creative/archive/rectangle/revision-05/audio/build_score.py
All synthesis, cue placement and gain decisions are defined here. No earlier
score, audio file, loop, soundfont, impulse response or recording is an input.
"""
from array import array
from pathlib import Path
import hashlib
import json
import math
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SR = 48000
DURATION = 18.000
N = int(SR * DURATION)
TAU = 2 * math.pi
SEED = 5101873
left, right = array('f', [0]) * N, array('f', [0]) * N
events = []


def midi(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def smooth(u):
    u = min(1., max(0., u))
    return u * u * (3 - 2 * u)


def env(t, duration, attack=.006, release=.08):
    return smooth(t / attack) * smooth((duration - t) / release)


def add(start, duration, fn, gain=1., pan=0., kind='', **details):
    """Equal-power pan for mono events; stereo synth voices get separate events."""
    begin = int(round(start * SR))
    count = min(int(round(duration * SR)), N - begin)
    l = math.cos((pan + 1) * math.pi / 4) * gain
    r = math.sin((pan + 1) * math.pi / 4) * gain
    for j in range(count):
        v = fn(j / SR)
        left[begin + j] += v * l
        right[begin + j] += v * r
    events.append(dict(kind=kind, start_s=start, duration_s=duration,
                       gain=gain, pan=pan, **details))


def kick(start, gain=.16):
    duration = .38
    # Integrated falling frequency, 54 Hz body; no click sample.
    def sound(t):
        phase = TAU * (54 * t + 95 * .018 * (1 - math.exp(-t / .018)))
        return math.sin(phase) * math.exp(-t / .092) * env(t, duration, .002, .04)
    add(start, duration, sound, gain, kind='dry sine kick', body_hz=54)


def rim(start, gain=.038, pan=.1):
    duration = .095
    rng = random.Random(SEED + int(start * SR))
    previous = 0.
    def sound(t):
        nonlocal previous
        white = rng.uniform(-1, 1)
        high = white - previous
        previous = white
        body = .56 * math.sin(TAU * 1620 * t) + .19 * math.sin(TAU * 2370 * t)
        return (body + .13 * high) * math.exp(-t / .016) * env(t, duration, .0007, .014)
    add(start, duration, sound, gain, pan, 'dry oscillator rim')


def tick(start, gain=.014, pan=-.17):
    duration = .075
    rng = random.Random(SEED * 2 + int(start * SR))
    low = 0.
    a = 1 - math.exp(-TAU * 4800 / SR)
    def sound(t):
        nonlocal low
        white = rng.uniform(-1, 1)
        low += a * (white - low)
        return (white - low) * math.exp(-t / .014) * env(t, duration, .001, .012)
    add(start, duration, sound, gain, pan, 'filtered-noise closed tick')


def bass(start, note, duration=.38, gain=.098):
    f = midi(note)
    def sound(t):
        p = TAU * f * t
        wave = math.sin(p) + .25 * math.sin(2 * p) + .085 * math.sin(3 * p)
        return math.tanh(wave * 1.05) * (.77 + .23 * math.exp(-t / .11)) * env(t, duration, .012, .10)
    add(start, duration, sound, gain, kind='warm harmonic oscillator bass', midi=note, frequency_hz=f)


def chord(start, duration, notes, gain=.018, label=''):
    for k, note in enumerate(notes):
        f = midi(note)
        detune = [-.0015, .0009, -.0007, .0012, -.0004][k % 5]
        pan = [-.42, .34, -.21, .43, 0][k % 5]
        def sound(t, f=f, detune=detune, k=k):
            p = TAU * f * t
            fundamental = .70 * math.sin(p) + .30 * math.sin(p * (1 + detune))
            harmonic = .08 * math.sin(2 * p + .15 * math.sin(TAU * .17 * t))
            # Gentle amplitude evolution, never a distracting obvious tremolo.
            evolution = .93 + .07 * math.sin(TAU * .105 * t + k * .4)
            return (fundamental + harmonic) * evolution * env(t, duration, .33, .65)
        add(start, duration, sound, gain, pan, 'evolving sine harmony', midi=note, harmony=label)


def pluck(start, note, gain=.035, duration=.7, pan=0., kind='soft oscillator pluck'):
    f = midi(note)
    def sound(t):
        p = TAU * f * t
        fm = .38 * math.sin(2 * p) * math.exp(-t / .10)
        tone = math.sin(p + fm) + .075 * math.sin(3 * p)
        return tone * math.exp(-t / .22) * env(t, duration, .005, .12)
    add(start, duration, sound, gain, pan, kind, midi=note, frequency_hz=f)


def ding():
    duration = 1.25
    f = midi(86)  # D6, one entrance cue with a small, quiet upper partial.
    def sound(t):
        return (math.sin(TAU * f * t) * math.exp(-t / .27)
                + .12 * math.sin(TAU * f * 2.003 * t) * math.exp(-t / .12)) * env(t, duration, .004, .12)
    add(.12, duration, sound, .044, -.08, 'single delicate source ding', fundamental_hz=f)


def noise_gesture(start, duration, gain, flight=False):
    rng = random.Random(SEED + (53 if flight else 29))
    lo = hi = 0.
    for j in range(int(duration * SR)):
        idx = round(start * SR) + j
        if idx >= N:
            break
        t, u = j / SR, j / SR / duration
        white = rng.uniform(-1, 1)
        upper = 1800 + (4500 * u * u if flight else 400 * u)
        a = 1 - math.exp(-TAU * upper / SR)
        b = 1 - math.exp(-TAU * (550 if flight else 420) / SR)
        hi += a * (white - hi)
        lo += b * (white - lo)
        band = hi - lo
        if flight:
            intensity = .12 + .88 * u * u
            pan = -.36 + .72 * u
            envelope = env(t, duration, .035, .035)
        else:
            intensity = .65 + .35 * math.sin(TAU * (7.5 * t + 1.2 * t * t)) ** 2
            pan = -.1
            envelope = env(t, duration, .16, .13)
        v = band * gain * intensity * envelope
        left[idx] += v * math.cos((pan + 1) * math.pi / 4)
        right[idx] += v * math.sin((pan + 1) * math.pi / 4)
    events.append(dict(kind='accelerating filtered air' if flight else 'quiet filtered friction',
                       start_s=start, duration_s=duration, gain=gain,
                       deterministic_seed=SEED + (53 if flight else 29)))


def compose():
    ding()
    # Sparse initial groove leaves the source clear. The last two seconds resolve.
    for t in [.50, 1.50, 2.50, 3.00, 4.00, 4.50, 5.50, 6.50,
              7.50, 8.50, 9.50, 10.00, 11.00, 12.00, 13.00, 14.00, 15.00]:
        kick(t, .145 if t < 4.5 else .16)
    for t in [1.00, 2.00, 3.50, 5.00, 6.00, 7.00, 8.00, 9.00,
              10.50, 11.50, 12.50, 13.50, 14.50]:
        rim(t, .030 if 3 <= t < 6.5 else .035)
    for k, t in enumerate([.75, 1.25, 1.75, 2.25, 2.75, 3.75, 4.25,
                           4.75, 5.25, 5.75, 6.25, 6.75, 7.25, 7.75,
                           8.25, 8.75, 9.25, 9.75, 10.25, 10.75,
                           11.25, 11.75, 12.25, 12.75, 13.25, 13.75,
                           14.25, 14.75]):
        tick(t, .011 + .003 * (k % 2), -.20 if k % 2 else .20)
    # Three tucked ghost ticks add increasing momentum solely during flight.
    for t, g in [(5.375, .008), (5.9375, .009), (6.3125, .010)]:
        tick(t, g, .08)

    for t, note, length, g in [
        (.5, 38, .43, .092), (1.5, 38, .35, .085), (2.25, 45, .25, .075),
        (2.5, 38, .37, .09), (3., 35, .39, .082), (4., 42, .30, .075),
        (4.5, 35, .43, .09), (5.5, 42, .37, .085), (6.5, 31, .56, .10),
        (7.5, 38, .36, .09), (8.5, 31, .43, .095), (9.5, 38, .32, .084),
        (10., 33, .50, .092), (11., 38, .42, .088), (12., 33, .46, .092),
        (13., 38, .42, .09), (14., 45, .42, .082), (15., 38, 1.15, .096)]:
        bass(t, note, length, g)

    chord(.32, 2.85, [50, 57, 59, 64, 66], .019, 'D6add9')
    chord(3., 3.80, [47, 54, 57, 61, 62], .018, 'Bm9')
    chord(6.5, 3.85, [43, 50, 54, 57, 59], .020, 'Gmaj9')
    chord(10., 5.35, [45, 50, 52, 54, 61], .021, 'Dmaj9/A')
    chord(15., 3.00, [50, 57, 59, 64, 66], .023, 'D6add9 final resolution')
    for t, note, p in [(1.25, 78, -.2), (2.25, 76, .22), (3.5, 73, -.16),
                       (7.25, 71, -.18), (8.25, 69, .18), (9.25, 66, -.1),
                       (11.25, 69, .20), (12.75, 66, -.15), (13.75, 64, .12)]:
        pluck(t, note, .026, .63, p)

    noise_gesture(3.0, 1.49, .017)
    rim(4.455, .021, 0.)
    noise_gesture(4.5, 2.045, .040, flight=True)
    # Restrained arrival articulates the receiving position precisely at 6.500.
    pluck(6.5, 67, .040, 1.0, -.05, 'restrained arrival tone')
    pluck(6.5, 74, .021, .85, .12, 'arrival harmonic')
    # The small opening has a common exact attack, with no notification melody.
    for n, g, p in [(74, .036, -.18), (78, .030, .10), (81, .024, .25)]:
        pluck(10., n, g, 1.05, p, 'Found harmonic opening')
    for n, g, p in [(62, .043, -.15), (69, .026, .08), (78, .020, .17)]:
        pluck(15., n, g, 1.35, p, 'final sign-off resolution')


def write_raw():
    raw = ROOT / '.synthesis-f32le.raw'
    interleaved = array('f')
    hp_l = hp_r = 0.
    a = 1 - math.exp(-TAU * 22 / SR)
    peak, sum_sq = 0., 0.
    for i in range(N):
        t = i / SR
        # Remove inaudible/DC content and close with a guaranteed zero boundary.
        hp_l += a * (left[i] - hp_l)
        hp_r += a * (right[i] - hp_r)
        fade = smooth(t / .012) * smooth((DURATION - t - 1 / SR) / .95)
        l, r = (left[i] - hp_l) * fade, (right[i] - hp_r) * fade
        interleaved.extend((l, r))
        peak = max(peak, abs(l), abs(r))
        sum_sq += l * l + r * r
    if sys.byteorder != 'little':
        interleaved.byteswap()
    raw.write_bytes(interleaved.tobytes())
    return raw, {'peak_dbfs': 20 * math.log10(peak),
                 'rms_dbfs': 10 * math.log10(sum_sq / (2 * N))}


def ffmpeg(args):
    result = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', *args],
                            capture_output=True, text=True, check=True)
    return result.stderr


def loudness(stderr):
    return json.loads(re.findall(r'\{[\s\S]*?\}', stderr)[-1])


def main():
    compose()
    raw, raw_stats = write_raw()
    inp = ['-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(raw)]
    measured = loudness(ffmpeg([*inp, '-af', 'loudnorm=I=-16:TP=-1:LRA=9:print_format=json', '-f', 'null', '-']))
    af = ('loudnorm=I=-16:TP=-1:LRA=9:linear=true:print_format=json'
          f':measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}'
          f':measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}'
          f':offset={measured["target_offset"]}')
    output = ROOT / 'jjintern-revision-05-original-score.wav'
    norm_report = loudness(ffmpeg(['-y', *inp, '-af', af, '-ar', str(SR), '-ac', '2',
                                 '-c:a', 'pcm_s24le', '-t', '18.000', str(output)]))
    validation = loudness(ffmpeg(['-i', str(output), '-af',
                                 'loudnorm=I=-16:TP=-1:LRA=9:print_format=json', '-f', 'null', '-']))
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                       '-show_format', '-of', 'json', str(output)], text=True))
    stream = probe['streams'][0]
    # This source check proves exact endpoints and bounds, not subjective listening.
    decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                      '-f', 'f32le', '-acodec', 'pcm_f32le', '-'])
    samples = array('f')
    samples.frombytes(decoded)
    if sys.byteorder != 'little':
        samples.byteswap()
    sample_peak = max(abs(v) for v in samples)
    assert len(samples) == 2 * N and float(stream['duration']) == DURATION
    assert sample_peak < 1 and all(v == 0 for v in samples[-2:])
    # An actual delivery-codec round trip checks that AAC does not lose headroom.
    aac_check = ROOT / '.aac-check.m4a'
    ffmpeg(['-y', '-i', str(output), '-c:a', 'aac', '-b:a', '256k', str(aac_check)])
    aac_measurement = loudness(ffmpeg(['-i', str(aac_check), '-af',
                                     'loudnorm=I=-16:TP=-1:LRA=9:print_format=json', '-f', 'null', '-']))
    aac_check.unlink()
    ffmpeg(['-y', '-i', str(output), '-filter_complex',
            'showwavespic=s=1800x420:split_channels=1:colors=0071e3|203145',
            '-frames:v', '1', '-update', '1', str(ROOT / 'waveform.png')])
    manifest = {
        'title': 'JJIntern revision 05 — original rectangle motion score',
        'created_for': 'approved revision-05 18-second advertisement',
        'source': 'build_score.py', 'output': output.name,
        'provenance': 'Newly composed and synthesized for this revision. Every sound originates in analytic oscillators, seeded pseudorandom noise, one-pole filters and amplitude envelopes. No audio assets are read by the synthesizer. FFmpeg only normalizes and encodes the resulting samples.',
        'external_audio_inputs': [], 'voiceover': False,
        'duration_seconds': DURATION, 'sample_rate_hz': SR,
        'channels': 2, 'pcm_bit_depth': 24, 'samples_per_channel': N,
        'tempo_bpm': 120, 'pulse_seconds': .5, 'random_seed': SEED,
        'harmony': ['D6add9', 'Bm9', 'Gmaj9', 'Dmaj9/A', 'D6add9'],
        'design': 'Dry sparse percussion, warm fundamental-rich oscillator bass, quiet evolving sine harmony, small tonal punctuation. Flight gains filtered air and three low-level ghost ticks; percussion stops at sign-off, leaving a warm resolved tail.',
        'synchronization': [
            {'at_s': .12, 'event': 'one delicate source ding'},
            {'from_s': 3.0, 'to_s': 4.49, 'event': 'quiet friction follows continuous compression'},
            {'at_s': 4.455, 'event': 'soft packet closure'},
            {'from_s': 4.5, 'to_s': 6.545, 'event': 'rising filtered air; 45 ms arrival tail'},
            {'at_s': 6.5, 'event': 'restrained tonal arrival and Gmaj9 harmony'},
            {'at_s': 10.0, 'event': 'small harmonic opening for Found'},
            {'at_s': 15.0, 'event': 'D6add9 sign-off resolution, percussion stops'},
            {'from_s': 17.05, 'to_s': 18.0, 'event': 'smooth final fade; last sample exactly zero'}],
        'mastering': {'target_integrated_lufs': -16, 'true_peak_ceiling_dbtp': -1,
                      'target_lra_lu': 9, 'normalization_type': norm_report.get('normalization_type'),
                      'raw_synthesis_stats': raw_stats},
        'measured_final': {'integrated_lufs': float(validation['input_i']),
                           'true_peak_dbtp': float(validation['input_tp']),
                           'loudness_range_lu': float(validation['input_lra']),
                           'sample_peak_dbfs': 20 * math.log10(sample_peak),
                           'duration_seconds': float(stream['duration']),
                           'sample_count_per_channel': len(samples) // 2,
                           'first_stereo_sample': list(samples[:2]),
                           'last_stereo_sample': list(samples[-2:]),
                           'clipped_samples': sum(abs(v) >= 1 for v in samples)},
        'aac_256k_roundtrip_check': {'integrated_lufs': float(aac_measurement['input_i']),
                                    'true_peak_dbtp': float(aac_measurement['input_tp']),
                                    'loudness_range_lu': float(aac_measurement['input_lra'])},
        'inspection': {'performed': ['exact duration/sample-count check', '48 kHz stereo PCM codec check',
                                     'integrated loudness and 4x true-peak analysis via FFmpeg loudnorm',
                                     'endpoint and clipping inspection', 'source/cue-event inspection',
                                     '256 kbps AAC encode/decode loudness and true-peak check',
                                     'stereo waveform image generated for visual inspection'],
                       'not_performed': ['human listening on headphones/speakers', 'physical-phone playback'],
                       'limitation': 'Synthesis and measurement were inspected; subjective listening is not claimed.'},
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'events': sorted(events, key=lambda e: e['start_s'])}
    (ROOT / 'audio-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'loudness-analysis.json').write_text(json.dumps({'first_pass': measured, 'normalization': norm_report,
                                                           'final_measurement': validation,
                                                           'aac_256k_roundtrip': aac_measurement}, indent=2) + '\n')
    raw.unlink()
    print(json.dumps({'output': str(output), 'measured_final': manifest['measured_final']}, indent=2))


if __name__ == '__main__':
    main()
