#!/usr/bin/env python3
"""JJIntern revision08: original electronic / breakbeat motion score.

Synthesis requires Python's standard library only. FFmpeg measures, masters,
encodes and draws the waveform. No audio file, sample, loop or impulse response
is an input. This is a new composition and synth design, not a shortened,
retimed, remixed or resampled earlier score.
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
SR, DURATION, SEED = 48000, 18.000, 80831081
N = round(SR * DURATION)
TAU = 2 * math.pi
BPM, BEAT = 144, 5 / 12
BUS = [array('f', [0]) * N, array('f', [0]) * N]
EVENTS = []


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def smooth(v):
    v = max(0., min(1., v))
    return v * v * (3 - 2 * v)


def edge(t, length, attack=.0015, release=.018):
    return smooth(t / attack) * smooth((length - t) / release)


def add(start, length, synth, gain, pan, kind, **parameters):
    begin = round(start * SR)
    count = min(round(length * SR), N - begin)
    lg = gain * math.cos((pan + 1) * math.pi / 4)
    rg = gain * math.sin((pan + 1) * math.pi / 4)
    for i in range(count):
        v = synth(i / SR)
        BUS[0][begin + i] += lg * v
        BUS[1][begin + i] += rg * v
    EVENTS.append(dict(start_s=start, duration_s=length, gain=gain, pan=pan, kind=kind, **parameters))


def kick(start, gain=.22, body=52, length=.24):
    rng = random.Random(SEED + round(start * SR) + 1)
    def synth(t):
        phase = TAU * (body * t + 122 * .012 * (1 - math.exp(-t / .012)))
        core = math.tanh(1.35 * math.sin(phase)) * math.exp(-t / .072)
        attack = rng.uniform(-1, 1) * .19 * math.exp(-t / .0025)
        return (core + attack) * edge(t, length, .0008, .027)
    add(start, length, synth, gain, 0, 'punchy clipped-sine kick', body_hz=body)


def snare(start, gain=.135, ghost=False):
    length = .11 if ghost else .17
    rng = random.Random(SEED + round(start * SR) + 5)
    lo = hi = 0.
    a, b = 1 - math.exp(-TAU * 9100 / SR), 1 - math.exp(-TAU * 650 / SR)
    def synth(t):
        nonlocal lo, hi
        white = rng.uniform(-1, 1)
        hi += a * (white - hi)
        lo += b * (white - lo)
        snap = (hi - lo) * .85 * math.exp(-t / (.023 if ghost else .037))
        body = (.41 * math.sin(TAU * 183 * t) + .22 * math.sin(TAU * 321 * t)) * math.exp(-t / .031)
        return math.tanh(1.35 * (snap + body)) * edge(t, length, .0009, .022)
    add(start, length, synth, gain, .07, 'ghost snare' if ghost else 'dry noise-and-oscillator snare')


def hat(start, gain=.024, pan=-.3, length=.046, cutoff=6700):
    rng = random.Random(SEED + round(start * SR) + 11)
    low = 0.
    a = 1 - math.exp(-TAU * cutoff / SR)
    def synth(t):
        nonlocal low
        white = rng.uniform(-1, 1)
        low += a * (white - low)
        metal = .065 * math.sin(TAU * 8131 * t) * math.sin(TAU * 5623 * t)
        return ((white - low) + metal) * math.exp(-t / .010) * edge(t, length, .0006, .01)
    add(start, length, synth, gain, pan, 'dry high-pass metallic tick', upper_noise_filter_hz=cutoff)


def bass(start, note, length=.21, gain=.13, bite=1.):
    """Band-limited saw harmonics into a resonant, envelope-driven state filter."""
    f = hz(note)
    low = band = 0.
    harmonics = [(h, (-1) ** (h + 1) / h) for h in range(1, 11)]
    def synth(t):
        nonlocal low, band
        phase = TAU * f * t
        saw = sum(weight * math.sin(h * phase) for h, weight in harmonics) * .63
        drive = math.tanh(2.6 * saw)
        cutoff = 190 + bite * 2150 * math.exp(-t / .052)
        coefficient = 2 * math.sin(math.pi * cutoff / SR)
        low += coefficient * band
        high = drive - low - .58 * band
        band += coefficient * high
        resonant = math.tanh(1.8 * low)
        sub = .30 * math.sin(phase)
        amp = (.72 + .28 * math.exp(-t / .07)) * edge(t, length, .003, .045)
        return (resonant * .75 + sub) * amp
    add(start, length, synth, gain, 0, 'gritty resonant bass stab', midi=note,
        fundamental_hz=f, harmonics=10, distortion_drive=2.6,
        filter_cutoff_start_hz=190 + bite * 2150, filter_cutoff_floor_hz=190,
        filter_envelope_decay_s=.052, filter_damping=.58)


def metal(start, carrier=540, gain=.055, length=.20, pan=0, ratio=2.73, kind='metallic FM hit'):
    def synth(t):
        p = TAU * carrier * t
        index = 8.5 * math.exp(-t / .026) + .35
        fm = math.sin(p + index * math.sin(p * ratio))
        ring = .14 * math.sin(p * 3.17) * math.sin(p * 1.413)
        return (fm + ring) * math.exp(-t / .047) * edge(t, length, .0008, .03)
    add(start, length, synth, gain, pan, kind, carrier_hz=carrier, modulator_ratio=ratio,
        initial_fm_index=8.85)


def click(start, gain=.065, frequency=2300, length=.035, pan=0, kind='mechanical sync click'):
    rng = random.Random(SEED + round(start * SR) + 19)
    low = 0.
    a = 1 - math.exp(-TAU * 6000 / SR)
    def synth(t):
        nonlocal low
        white = rng.uniform(-1, 1)
        low += a * (white - low)
        tone = math.sin(TAU * frequency * t)
        return (.42 * low + .58 * tone) * math.exp(-t / .0047) * edge(t, length, .0004, .007)
    add(start, length, synth, gain, pan, kind, frequency_hz=frequency)


def source_ding():
    f, length = hz(90), .66
    def synth(t):
        main = math.sin(TAU * f * t) * math.exp(-t / .205)
        bright = .24 * math.sin(TAU * f * 2.01 * t) * math.exp(-t / .08)
        return (main + bright) * edge(t, length, .0015, .08)
    add(.18, length, synth, .115, 0, 'prominent isolated source ding', fundamental_hz=f)


def zipper(start, length, gain, descending=False, kind='filtered zipper texture'):
    rng = random.Random(SEED + round(start * SR) + 23)
    low = high = 0.
    phase = 0.
    def synth(t):
        nonlocal low, high, phase
        u = t / length
        white = rng.uniform(-1, 1)
        cutoff = 650 + 6700 * ((1 - u) ** 2 if descending else u ** 2)
        high += (1 - math.exp(-TAU * cutoff / SR)) * (white - high)
        low += (1 - math.exp(-TAU * 430 / SR)) * (white - low)
        phase += TAU * (24 + 78 * u) / SR
        grain = .32 + .68 * max(0, math.sin(phase)) ** 3
        return (high - low) * grain * edge(t, length, .009, .012)
    add(start, length, synth, gain, -.06, kind, direction='down' if descending else 'up')


def flight_air():
    start, length = 3.1, 5.0
    rng = random.Random(SEED + 310)
    low = high = 0.
    phase = 0.
    for j in range(round(length * SR)):
        t, u = j / SR, j / SR / length
        white = rng.uniform(-1, 1)
        cutoff = 1900 + 6200 * u ** 1.7
        high += (1 - math.exp(-TAU * cutoff / SR)) * (white - high)
        low += (1 - math.exp(-TAU * 280 / SR)) * (white - low)
        phase += TAU * (570 + 1180 * u * u) / SR
        # Aerodynamic grain rather than sustained full-volume white noise.
        grain = .78 + .22 * math.sin(TAU * (17 * t + 4 * t * t))
        air = (high - low) * grain + .042 * math.sin(phase)
        level = .048 * (.32 + .68 * u ** 1.8) * edge(t, length, .018, .016)
        pan = -.45 + .90 * u
        idx = round(start * SR) + j
        BUS[0][idx] += level * air * math.cos((pan + 1) * math.pi / 4)
        BUS[1][idx] += level * air * math.sin((pan + 1) * math.pi / 4)
    EVENTS.append(dict(start_s=start, duration_s=length, kind='five-second textured air-resistance rise',
                       gain=.048, initial_level_fraction=.32, cutoff_start_end_hz=[1900, 8100],
                       pan_start_end=[-.45, .45], deterministic_noise_seed=SEED + 310))
    # Fast initial streak rhythm already moves; rate increases continuously.
    phase_fn = lambda u: 5 * (3.2 * u + 8.8 * u ** 3 / 3)
    for target in range(1, math.floor(phase_fn(1)) + 1):
        lo, hi = 0., 1.
        for _ in range(42):
            middle = (lo + hi) / 2
            if phase_fn(middle) < target:
                lo = middle
            else:
                hi = middle
        u = (lo + hi) / 2
        at = start + length * u
        if at < 8.035:
            hat(at, .012 + .009 * u, -.30 + .60 * u, .030, 5300 + 2400 * u)
            EVENTS[-1]['kind'] = 'accelerating air-rhythm tick'
            EVENTS[-1]['normalized_flight_progress'] = u


def break_bar(start, variation):
    """Syncopation comes from kick and bass placement, not a straight house loop."""
    kick_steps = [[0, 1.5, 2.75], [0, .75, 2, 2.5], [0, 1.75, 2.5, 3.5]][variation % 3]
    for step in kick_steps:
        kick(start + BEAT * step, .21 if step in (0, 2) else .17)
    for step in (1, 3):
        snare(start + BEAT * step, .128)
    if variation == 1:
        snare(start + BEAT * 2.75, .048, True)
    if variation == 2:
        snare(start + BEAT * 3.75, .052, True)
    riffs = [
        [(0, 30, .26), (.75, 30, .13), (1.5, 37, .17), (2.75, 40, .16)],
        [(0, 30, .22), (.75, 42, .14), (2, 37, .23), (3.5, 33, .13)],
        [(0, 30, .26), (1.75, 40, .15), (2.5, 37, .15), (3.5, 30, .15)]]
    for step, note, length in riffs[variation % 3]:
        bass(start + BEAT * step, note, length, .125, 1 + .15 * variation)


def tail_delay(start, carrier, gain, pan):
    # Every repeat is synthesized independently from the same analytic FM formula.
    # Repeats lose upper harmonics and decay in gain; no recorded impulse is used.
    for k in range(7):
        at = start + k * .245
        metal(at, carrier, gain * .48 ** k, .23 + .025 * k,
              pan if k % 2 == 0 else -pan, 2.73 - .08 * k, 'synthesized rhythmic tail repeat')


def compose():
    source_ding()
    # The opening ding is isolated; drums first enter at 0.600 seconds.
    kick(.60, .17)
    bass(.60, 30, .22, .11)
    snare(1.0166666667, .105)
    hat(.8083333333, .019, -.22)
    kick(1.4333333333, .175)
    bass(1.4333333333, 37, .19, .105)
    hat(1.6416666667, .023, .20)
    snare(1.85, .075, True)
    metal(1.72, 416, .026, .13, -.19)

    # Intricate 550 ms morph: three discrete actions and a separate final lock.
    zipper(2.0, .55, .039, False, 'morph granulation and friction')
    click(2.08, .068, 2860, .029, -.22, 'morph sync click one')
    click(2.24, .075, 2140, .031, .14, 'morph sync click two')
    click(2.42, .080, 1650, .033, -.08, 'morph sync click three')
    metal(2.55, 335, .065, .12, 0, 1.71, 'packet lock')
    # Silence after the lock allows the packet pause to read.
    zipper(3.035, .065, .034, False, 'short launch intake')
    click(3.1, .040, 1200, .028, -.25, 'launch edge')
    for bar in range(3):
        break_bar(3.1 + bar * 4 * BEAT, bar)
    for t, f, p in [(3.725, 510, -.25), (4.5583333333, 735, .25),
                    (5.8083333333, 620, -.18), (6.85, 830, .18), (7.6833333333, 470, -.16)]:
        metal(t, f, .035, .16, p)
    flight_air()

    # Contact, swallow and latch are three separate sounds with breathing room.
    kick(8.1, .265, 43, .34)
    bass(8.1, 30, .36, .14, 1.3)
    metal(8.1, 270, .10, .24, .05, 1.63, 'receiver contact impact')
    zipper(8.82, .36, .072, True, 'receiver swallow filter fall')
    click(9.05, .077, 920, .035, -.04, 'receiver swallowed latch')
    metal(9.25, 382, .064, .13, 0, 1.37, 'receiver final lock')

    # Found opens an octave/fifth power stab, with no sustained pad or jazz chord.
    kick(10.2, .23)
    bass(10.2, 30, .32, .14, 1.05)
    metal(10.2, hz(54), .064, .27, -.15, 2.0, 'Found octave power accent')
    metal(10.2, hz(61), .036, .23, .15, 2.0, 'Found fifth accent')
    for t, n, length in [(10.825, 37, .17), (11.45, 30, .22),
                         (12.075, 40, .17), (12.7, 37, .20), (13.325, 30, .17)]:
        bass(t, n, length, .115, .9)
    for t in [11.0333333333, 11.8666666667, 12.7, 13.325]:
        kick(t, .17)
    for t in [10.6166666667, 11.45, 12.2833333333, 13.1166666667]:
        snare(t, .105)
    for k, t in enumerate([10.4083333333, 10.825, 11.2416666667, 11.6583333333,
                           12.075, 12.4916666667, 12.9083333333, 13.5333333333]):
        hat(t, .019, -.23 if k % 2 else .23)
    click(11.1, .025, 1720, .027, -.13, 'first payoff line edit tick')
    click(11.35, .025, 2190, .027, .13, 'second payoff line edit tick')
    # Brief pre-resolve pocket makes the brand sign-off a deliberate downbeat.
    kick(14.0, .245, 46, .32)
    bass(14.0, 30, .48, .145, .85)
    metal(14.0, hz(54), .08, .30, -.10, 2.0, 'brand resolve octave')
    metal(14.0, hz(61), .039, .25, .12, 2.0, 'brand resolve fifth')
    for t, n, g in [(14.625, 37, .10), (15.25, 30, .085)]:
        kick(t, .16 if t < 15 else .13)
        bass(t, n, .18, g, .75)
    snare(14.4166666667, .090)
    snare(15.0416666667, .068)
    snare(15.6666666667, .047, True)
    for t, g in [(14.2083333333, .019), (14.8333333333, .017),
                 (15.4583333333, .014), (15.875, .011)]:
        hat(t, g, -.15)
    tail_delay(15.58, 467, .035, .32)


def write_raw():
    raw = ROOT / '.synthesis-f32le.raw'
    interleaved = array('f')
    low = [0., 0.]
    a = 1 - math.exp(-TAU * 25 / SR)
    peak, energy = 0., 0.
    for i in range(N):
        t = i / SR
        # Short gaps serve the mechanics and sign-off; score is otherwise continuous.
        gate = 1.
        if 2.72 <= t < 3.025:
            gate = 0.
        elif 2.70 <= t < 2.72:
            gate = 1 - smooth((t - 2.70) / .020)
        elif 13.83 <= t < 13.87:
            gate = 1 - smooth((t - 13.83) / .04)
        elif 13.87 <= t < 14.0:
            gate = 0.
        fade = smooth(t / .005) * smooth((DURATION - t - 1 / SR) / .35)
        for ch in range(2):
            low[ch] += a * (BUS[ch][i] - low[ch])
            v = (BUS[ch][i] - low[ch]) * gate * fade
            interleaved.append(v)
            peak = max(peak, abs(v))
            energy += v * v
    if sys.byteorder != 'little':
        interleaved.byteswap()
    raw.write_bytes(interleaved.tobytes())
    return raw, dict(peak_dbfs=20 * math.log10(peak), rms_dbfs=10 * math.log10(energy / (2 * N)))


def ffmpeg(args):
    process = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', *args],
                             capture_output=True, text=True, check=True)
    return process.stderr


def report(stderr):
    return json.loads(re.findall(r'\{[\s\S]*?\}', stderr)[-1])


def main():
    compose()
    raw, raw_stats = write_raw()
    inp = ['-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(raw)]
    target = 'loudnorm=I=-14.5:TP=-1.2:LRA=9:print_format=json'
    first = report(ffmpeg([*inp, '-af', target, '-f', 'null', '-']))
    af = ('loudnorm=I=-14.5:TP=-1.2:LRA=9:linear=true:print_format=json'
          f':measured_I={first["input_i"]}:measured_TP={first["input_tp"]}'
          f':measured_LRA={first["input_lra"]}:measured_thresh={first["input_thresh"]}'
          f':offset={first["target_offset"]}')
    output = ROOT / 'jjintern-revision-08-original-score.wav'
    normalization = report(ffmpeg(['-y', *inp, '-af', af, '-ar', str(SR), '-ac', '2',
                                   '-c:a', 'pcm_s24le', '-t', '18.000', str(output)]))
    measurement = report(ffmpeg(['-i', str(output), '-af', target, '-f', 'null', '-']))
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                       '-show_format', '-of', 'json', str(output)], text=True))
    decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                      '-f', 'f32le', '-acodec', 'pcm_f32le', '-'])
    samples = array('f')
    samples.frombytes(decoded)
    if sys.byteorder != 'little':
        samples.byteswap()
    peak = max(abs(v) for v in samples)
    assert len(samples) == 2 * N and float(probe['streams'][0]['duration']) == DURATION
    assert peak < 1 and all(v == 0 for v in samples[-2:])
    flight_ticks = [e['start_s'] for e in EVENTS if e['kind'] == 'accelerating air-rhythm tick']
    intervals = [b - a for a, b in zip(flight_ticks, flight_ticks[1:])]
    assert all(b < a for a, b in zip(intervals, intervals[1:]))
    aac = ROOT / '.aac-check.m4a'
    ffmpeg(['-y', '-i', str(output), '-c:a', 'aac', '-b:a', '256k', str(aac)])
    aac_measurement = report(ffmpeg(['-i', str(aac), '-af', target, '-f', 'null', '-']))
    aac.unlink()
    ffmpeg(['-y', '-i', str(output), '-filter_complex',
            'showwavespic=s=1800x420:split_channels=1:colors=0071e3|203145',
            '-frames:v', '1', '-update', '1', str(ROOT / 'waveform.png')])
    manifest = {
        'title': 'JJIntern revision08 — original electronic breakbeat showreel cue',
        'source': 'build_score.py', 'output': output.name,
        'provenance': 'New composition and timbre design. Every sound is produced from analytic oscillators, seeded noise, resonant filters, saturation and envelopes. No previous audio, samples, recordings, stock loops, soundfonts, voiceover or impulse-response files are used. Rhythmic tail repeats are synthesized analytically.',
        'external_audio_inputs': [], 'voiceover': False,
        'duration_seconds': DURATION, 'sample_rate_hz': SR, 'channels': 2,
        'pcm_bit_depth': 24, 'samples_per_channel': N,
        'tempo_bpm': BPM, 'beat_seconds': BEAT, 'random_seed': SEED,
        'tonal_palette': 'F-sharp minor/pentatonic bass riff; octave/fifth power accents; no chord pads.',
        'structure': 'Isolated ding; sparse broken opening; mechanical morph; packet silence; three 144 BPM breakbeat bars spanning the full five-second flight; separate contact/swallow/lock; Found and readable payoff groove; 14-second brand downbeat; two-second rhythmic tail; decaying FM echoes.',
        'timbre_changes_from_prior_revisions': ['No sustained pads or major-ninth harmony', 'No soft pluck motif',
            'Ten-harmonic saw bass through saturation and a resonant envelope filter',
            'Dry noise/body snares and syncopated kick patterns', 'High-index metallic FM accents',
            'Deliberate packet and pre-sign-off silence', '144 BPM broken rhythm instead of half-time lounge groove'],
        'synchronization': [
            {'at_s': .18, 'event': 'prominent isolated editorial source ding'},
            {'from_s': 2.0, 'to_s': 2.55, 'event': 'fast granular morph texture'},
            {'at_s': 2.08, 'event': 'morph sync click one'},
            {'at_s': 2.24, 'event': 'morph sync click two'},
            {'at_s': 2.42, 'event': 'morph sync click three'},
            {'at_s': 2.55, 'event': 'packet lock'},
            {'from_s': 2.72, 'to_s': 3.025, 'event': 'quiet packet pause'},
            {'at_s': 3.1, 'event': 'launch and first breakbeat downbeat'},
            {'from_s': 3.1, 'to_s': 8.1, 'event': 'five-second accelerating air resistance, rhythm and brightness'},
            {'at_s': 8.1, 'event': 'receiver contact impact'},
            {'at_s': 9.05, 'event': 'swallowed latch within descending filtered texture'},
            {'at_s': 9.25, 'event': 'short final receiver lock'},
            {'at_s': 10.2, 'event': 'Found octave/fifth accent'},
            {'at_s': 11.1, 'event': 'first line edit tick'},
            {'at_s': 11.35, 'event': 'second line edit tick'},
            {'from_s': 13.87, 'to_s': 14.0, 'event': 'pre-resolve pocket'},
            {'at_s': 14.0, 'event': 'strong brand resolve'},
            {'from_s': 14.0, 'to_s': 16.0, 'event': 'tapered rhythmic tail'},
            {'from_s': 16.0, 'to_s': 18.0, 'event': 'decaying synthesized FM repeats, then zero endpoint'}],
        'flight_rhythm': {'instantaneous_rate_hz_start_end': [3.2, 12.0],
                          'integrated_phase': '5 * (3.2*u + 8.8*u^3/3)',
                          'tick_times_s': flight_ticks, 'intervals_s': intervals,
                          'strictly_decreasing_intervals_verified': True},
        'mastering': {'target_integrated_lufs': -14.5, 'true_peak_ceiling_dbtp': -1.2,
                      'normalization_type': normalization['normalization_type'], 'raw_synthesis_stats': raw_stats},
        'measured_final': {'integrated_lufs': float(measurement['input_i']),
                           'true_peak_dbtp': float(measurement['input_tp']),
                           'loudness_range_lu': float(measurement['input_lra']),
                           'sample_peak_dbfs': 20 * math.log10(peak),
                           'duration_seconds': float(probe['streams'][0]['duration']),
                           'samples_per_channel': len(samples) // 2,
                           'last_stereo_sample': list(samples[-2:]),
                           'clipped_samples': sum(abs(v) >= 1 for v in samples)},
        'aac_256k_roundtrip_check': {'integrated_lufs': float(aac_measurement['input_i']),
                                    'true_peak_dbtp': float(aac_measurement['input_tp'])},
        'inspection': {'performed': ['source and timing inspection', 'duration/sample count/codec verification',
                                     'integrated loudness and true-peak analysis', 'endpoints and clipping',
                                     'accelerating flight interval verification', '256 kbps AAC encode/decode check',
                                     'waveform image generated for visual inspection'],
                       'not_performed': ['subjective human listening', 'physical-phone playback'],
                       'limitation': 'Synthesis architecture, timing and measurements were inspected; subjective listening is not claimed.'},
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'events': sorted(EVENTS, key=lambda e: e['start_s'])}
    (ROOT / 'audio-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (ROOT / 'loudness-analysis.json').write_text(json.dumps(dict(first_pass=first, normalization=normalization,
        final_measurement=measurement, aac_256k_roundtrip=aac_measurement), indent=2) + '\n')
    raw.unlink()
    print(json.dumps(dict(output=str(output), measured_final=manifest['measured_final'],
                         aac_256k_roundtrip=manifest['aac_256k_roundtrip_check']), indent=2))


if __name__ == '__main__':
    main()
